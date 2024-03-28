import os
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__, template_folder='templates')

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["TEMPLATES_AUTO_RELOAD"] = True

Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    rows = db.execute("SELECT symbol, SUM(shares) as total_shares FROM transactions WHERE user_id = :user_id GROUP BY symbol HAVING total_shares > 0",
                      user_id=session["user_id"])
    stocks = []
    total_cash = db.execute("SELECT cash FROM users WHERE id = :user_id", user_id=session["user_id"])[0]["cash"]
    total_value = 0

    for row in rows:
        stock = lookup(row["symbol"])
        if stock is not None:
            value = stock["price"] * row["total_shares"]
            total_value += value
            stocks.append({
                "symbol": stock["symbol"],
                "name": stock["name"],
                "shares": row["total_shares"],
                "price": usd(stock["price"]),
                "total": usd(value)
            })

    return render_template("index.html", stocks=stocks, cash=usd(total_cash), total=usd(total_cash + total_value))


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        symbol = request.form.get("symbol")
        shares = request.form.get("shares")
        if not symbol:
            return apology("must provide stock symbol")
        elif not shares:
            return apology("must provide number of shares")
        try:
            shares = int(shares)
        except ValueError:
            return apology("number of shares must be an integer")

        if shares <= 0:
            return apology("number of shares must be positive")

        quote = lookup(symbol)
        if not quote:
            return apology("invalid stock symbol")

        total_price = quote["price"] * shares
        user = db.execute("SELECT * FROM users WHERE id = :user_id", user_id=session["user_id"])[0]
        if user["cash"] < total_price:
            return apology("not enough cash")

        db.execute("UPDATE users SET cash = cash - :total_price WHERE id = :user_id",
                   total_price=total_price, user_id=session["user_id"])
        db.execute("INSERT INTO transactions (user_id, symbol, shares, price) VALUES (:user_id, :symbol, :shares, :price)",
                   user_id=session["user_id"], symbol=quote["symbol"], shares=shares, price=quote["price"])

        flash("Bought!")
        return redirect("/")

    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    transactions = db.execute(
        "SELECT symbol, shares, price, transacted FROM transactions WHERE user_id = :user_id ORDER BY transacted DESC",
        user_id=session["user_id"]
    )
    for transaction in transactions:
        transaction["price"] = usd(transaction["price"])
    return render_template("history.html", transactions=transactions)



@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    session.clear()

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username:
            return apology("must provide username")
        elif not password:
            return apology("must provide password")

        user = db.execute("SELECT * FROM users WHERE username = :username", username=username)
        if not user or not check_password_hash(user[0]["hash"], password):
            return apology("invalid username and/or password")

        session["user_id"] = user[0]["id"]
        return redirect("/")

    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""
    session.clear()
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote"""
    if request.method == "POST":
        symbol = request.form.get("symbol")
        if not symbol:
            return apology("must provide stock symbol")

        quote = lookup(symbol)
        if not quote:
            return apology("invalid stock symbol")

        return render_template("quoted.html", quote=quote)

    else:
                return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Ensure username was submitted
        if not username:
            return apology("must provide username")

        # Ensure password was submitted
        elif not password:
            return apology("must provide password")

        # Ensure password and confirmation match
        elif password != confirmation:
            return apology("passwords must match")

        # Hash password
        hashed_password = generate_password_hash(password)

        # Add user to the database
        try:
            db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)",
                       username=username, hash=hashed_password)
        except:
            return apology("username already exists")

        # Redirect user to login page
        flash("Registered!")
        return redirect("/login")

    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "POST":
        symbol = request.form.get("symbol")
        shares = request.form.get("shares")
        if not symbol:
            return apology("must provide stock symbol")
        elif not shares:
            return apology("must provide number of shares")
        try:
            shares = int(shares)
        except ValueError:
            return apology("number of shares must be an integer")

        if shares <= 0:
            return apology("number of shares must be positive")

        quote = lookup(symbol)
        if not quote:
            return apology("invalid stock symbol")

        user_shares = db.execute("SELECT SUM(shares) as total_shares FROM transactions WHERE user_id = :user_id AND symbol = :symbol GROUP BY symbol",
                                 user_id=session["user_id"], symbol=symbol)
        if not user_shares or user_shares[0]["total_shares"] < shares:
            return apology("not enough shares")

        total_price = quote["price"] * shares
        db.execute("UPDATE users SET cash = cash + :total_price WHERE id = :user_id",
                   total_price=total_price, user_id=session["user_id"])
        db.execute("INSERT INTO transactions (user_id, symbol, shares, price) VALUES (:user_id, :symbol, :shares, :price)",
                   user_id=session["user_id"], symbol=quote["symbol"], shares=-shares, price=quote["price"])

        flash("Sold!")
        return redirect("/")

    else:
        stocks = db.execute("SELECT symbol FROM transactions WHERE user_id = :user_id GROUP BY symbol HAVING SUM(shares) > 0",
                            user_id=session["user_id"])
        return render_template("sell.html", stocks=stocks)


if __name__ == "__main__":
    app.run(debug=True)


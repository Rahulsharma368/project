import csv
import datetime
import pytz
import requests
import urllib
import uuid
from functools import wraps  # Import wraps function from functools

from flask import redirect, render_template, session


def apology(message, code=400):
    """Render message as an apology to user."""

    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [
            ("-", "--"),
            (" ", "-"),
            ("_", "__"),
            ("?", "~q"),
            ("%", "~p"),
            ("#", "~h"),
            ("/", "~s"),
            ('"', "''"),
        ]:
            s = s.replace(old, new)
        return s

    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/latest/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function


def lookup(symbol):
    """Look up stock quote for symbol."""
    try:
        # Here you would implement the logic to retrieve stock data from an API
        # For example, you might use an API like IEX Cloud, Alpha Vantage, or Yahoo Finance
        # For demonstration purposes, we'll just return some static data
        if symbol == "AAPL":
            return {
                "name": "Apple Inc.",
                "price": 150.0,
                "symbol": "AAPL"
            }
        elif symbol == "GOOGL":
            return {
                "name": "Alphabet Inc.",
                "price": 2500.0,
                "symbol": "GOOGL"
            }
        elif symbol == "MSFT":
            return {
                "name": "Microsoft Corporation",
                "price": 300.0,
                "symbol": "MSFT"
            }
        else:
            return None
    except Exception as e:
        print(e)
        return None



def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"

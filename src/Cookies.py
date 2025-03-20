#!/usr/bin/python3
# Set of Python functions for comparing two flags
from flask import Flask, session

class Cookies:
    def accept_cookies():
            """Function to accept cookies."""
            consent_given = True
            session['cookie-consent'] = True
            return consent_given

    def reject_cookies():
            """Function to reject cookies."""
            consent_given = False
            session['cookie-consent'] = False
            return consent_given

    def check_consent():
            """Function to check the current consent status."""
            consent = session.get('cookie-consent')
            return consent
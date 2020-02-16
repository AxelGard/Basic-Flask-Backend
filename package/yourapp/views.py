from main import app
import forms
from flask import render_template, abort, session, flash, redirect, request


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/hello/')
def hello():
    return 'Hello, World'

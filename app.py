import os

from flask import Flask
from flask_restplus import Api, Resource
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SQALCHEMY_DATABASE_URL"] = os.getenv("APP_SQL_URL")
db = SQLAlchemy(app)
api = Api(app, title="Review Requester")


class Reviewer(db.Model):
    pass


class ReviewLanguage(db.Model):
    pass


class ReviewRequest(db.Model):
    pass


reviewers = api.namespace("reviewers", description="Reviewer Management")


@reviewers.route("/")
class ReviewerList(Resource):
    def get(self):
        """List of reviewer"""
        pass

    def post(self):
        """Add a reviewer."""
        pass


@reviewers.route("/<int:id>")
class ReviewerManagment(Resource):
    def get(self):
        """Retrieve a single reviewer."""
        pass

    def put(self):
        """Update a reviewer."""
        pass

    def delete(self):
        """Remove a reviewer."""
        pass


reviews = api.namespace("reviews", description="Review Request Data")


@reviews.route("/")
class Reviews(Resource):
    def get(self):
        """List of reviews."""
        pass


@app.route("/")
def main_page():
    """Display reviewers to request."""
    pass


@app.route("/manage")
def manage_reviewers():
    """Allow reviewer management."""
    pass


@app.route("/manage/<int:reviewer_id>")
def edit_reviewer(reviewer_id):
    """Edit a reviewer's details."""
    pass

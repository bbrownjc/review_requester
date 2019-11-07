import os

from flask import Flask
from flask_restplus import Api, Resource
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("APP_SQL_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
api = Api(app, title="Review Requester")


reviewer_languages = db.Table('reviewer_languages',
    db.Column('reviewer_id', db.Integer, db.ForeignKey('reviewer.id'), primary_key=True),
    db.Column('review_language_id', db.Integer, db.ForeignKey('review_language.id'), primary_key=True)
)


class Reviewer(db.Model):
    __tablename__ = 'reviewer'

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email_address = db.Column(db.String(50), unique=True, nullable=False)
    reviewer_languages = db.relationship('ReviewLanguage', secondary=reviewer_languages,
                                         lazy='subquery', backref=db.backref('pages', lazy=True))

    __table_args__ = (db.UniqueConstraint('last_name', 'first_name', name='name_uix'), )

    def __repr__(self):
        return '<Reviewer %r>' % self.id

class ReviewLanguage(db.Model):
    __tablename__ = 'review_language'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self):
        return '<Language %r>' % self.name

class ReviewRequest(db.Model):
    __tablename__ = 'review_request'

    id = db.Column(db.Integer, primary_key=True)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('reviewer.id'), nullable=False)
    review_language_id = db.Column(db.Integer, db.ForeignKey('review_language.id'), nullable=False)
    review_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        db.Index('review_date_ix', 'review_date'),
        db.Index('reviewer_ix', 'reviewer_id', 'review_language_id'),
    )

    def __repr__(self):
        return '<Review %r for Reviewer %r>' % (self.review_id, self.reviewer_id)


# Create the database and tables...
db.create_all()

reviewers = api.namespace("reviewers", description="Reviewer Management")

#################
# API Endpoints #
#################


@reviewers.route("/")
class ReviewerList(Resource):
    def get(self):
        """List of reviewers."""
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

    def post(self):
        """Add a review."""
        pass

################
# UI Endpoints #
################


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

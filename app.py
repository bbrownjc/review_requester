import datetime
import os

from flask import abort, Blueprint, Flask, redirect, render_template, request, url_for
from flask_restplus import Api, Resource
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("APP_SQL_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
api = Api(app, title="Review Requester")

api_app = Blueprint("api",  __name__, url_prefix="/api")
api = Api(title="Review Requester", doc="/docs")
api.init_app(api_app)
app.register_blueprint(api_app)

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
    languages = db.relationship('ReviewLanguage', secondary=reviewer_languages,
                                         lazy='subquery', backref=db.backref('reviewers', lazy=True))

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
        return '<Review %r for Reviewer %r>' % (self.id, self.reviewer_id)


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


REVIEWERS = [
    {
        "id": 5,
        "first_name": "Bob",
        "last_name": "Jones",
        "languages": ["python"],
        "review_count": 69,
        "last_review": datetime.date(2019, 4, 20)
    }, {
        "id": 6,
        "first_name": "Frank",
        "last_name": "Avery",
        "languages": ["python", "go"],
        "review_count": 42,
        "last_review": datetime.date(1970, 1, 1)
    }
]


LANGUAGES = [
    {"name": "python", "id":  1},
    {"name": "go", "id": 2}
]


@app.route("/")
def main_page():
    """Display reviewers to request."""
    language_id = request.args.get("language") or None
    language = [
        x["name"] for x in LANGUAGES if str(x["id"]) == language_id
    ][0] if language_id else None

    sort_key = request.args.get("sort") or "last_name"
    order = request.args.get("order") or "asc"
    reverse = order == "asc"

    # TODO: This filter and sorting will both need to be adapted
    # to become a sqlalchemy query once that portion of the code is in place
    reviewers = filter(
        lambda x: language in x["languages"], REVIEWERS
    ) if language else REVIEWERS
    reviewers = sorted(
        reviewers,
        key=lambda x: x[sort_key],
        reverse=reverse
    )

    return render_template(
        "reviewers.html",
        reviewers=reviewers,
        languages=LANGUAGES,
        sort=sort_key,
        link_order="desc" if order == "asc" else "asc"
    )


@app.route("/submit", methods=["POST"])
def open_mail():
    assignees = request.form.getlist("check")

    # TODO: Will need to retrieve actual emails from DB
    mails = [f"{id_}@junk.com" for id_ in assignees]

    redirect(f"mailto:{','.join(mails)}")


@app.route("/manage/<int:reviewer_id>")
def edit_reviewer(reviewer_id):
    """Edit a reviewer's details."""
    # TODO: use get actual use by ID from psql
    reviewers = [x for x in REVIEWERS if x["id"] == reviewer_id]

    if len(reviewers) != 1:
        abort(404)
    reviewer = reviewers[0]
    return render_template(
        "edit_reviewer.html", reviewer=reviewer, languages=LANGUAGES
    )


@app.route("/manage/edit_reviewer/<int:reviewer_id>", methods=["POST"])
def update_reviewer(reviewer_id):
    """Push updated reviewer data to database."""
    user = {
        "first_name": request.form.get("first_name"),
        "last_name": request.form.get("last_name"),
        "languages": request.form.getlist("languages")
    }
    # TODO: update user in psql
    return redirect(url_for("main_page"))

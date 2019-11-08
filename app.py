from datetime import datetime
import os

from flask import abort, Blueprint, Flask, redirect, render_template, request, url_for
from flask_restplus import Api, Resource
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import asc, desc, func

from data import LANGUAGE_DATA, REVIEWER_DATA

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("APP_SQL_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

api_app = Blueprint("api", __name__, url_prefix="/api")
api = Api(title="Review Requester", doc="/docs")
api.init_app(api_app)
app.register_blueprint(api_app)


reviewer_languages = db.Table(
    "reviewer_languages",
    db.Column(
        "reviewer_id", db.Integer, db.ForeignKey("reviewer.id"), primary_key=True
    ),
    db.Column(
        "review_language_id",
        db.Integer,
        db.ForeignKey("review_language.id"),
        primary_key=True,
    ),
)


class Reviewer(db.Model):
    __tablename__ = "reviewer"

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email_address = db.Column(db.String(50), unique=True, nullable=False)
    languages = db.relationship(
        "ReviewLanguage",
        secondary=reviewer_languages,
        lazy="subquery",
        backref=db.backref("reviewers", lazy=True),
    )

    __table_args__ = (db.UniqueConstraint("last_name", "first_name", name="name_uix"),)

    def __repr__(self):
        return "<Reviewer %r>" % self.id


class ReviewLanguage(db.Model):
    __tablename__ = "review_language"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self):
        return "<Language %r>" % self.name


class ReviewRequest(db.Model):
    __tablename__ = "review_request"

    id = db.Column(db.Integer, primary_key=True)
    reviewer_id = db.Column(db.Integer, db.ForeignKey("reviewer.id"), nullable=False)
    review_language_id = db.Column(
        db.Integer, db.ForeignKey("review_language.id"), nullable=False
    )
    review_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        db.Index("review_date_ix", "review_date"),
        db.Index("reviewer_ix", "reviewer_id", "review_language_id"),
    )

    def __repr__(self):
        return "<Review %r for Reviewer %r>" % (self.id, self.reviewer_id)


# Create the database and tables...
db.create_all()
LANGUAGES = {}
for language in LANGUAGE_DATA:
    language_entry = ReviewLanguage.query.filter_by(name=language).first()
    if not language_entry:
        language_entry = ReviewLanguage(name=language)
        db.session.add(language_entry)
    LANGUAGES[language] = language_entry
db.session.commit()

for reviewer in REVIEWER_DATA:
    reviewer_entry = Reviewer.query.filter_by(
        first_name=reviewer[0], last_name=reviewer[1]
    ).first()
    if not reviewer_entry:
        reviewer_entry = Reviewer()
        db.session.add(reviewer_entry)
    reviewer_entry.first_name = reviewer[0]
    reviewer_entry.last_name = reviewer[1]
    reviewer_entry.email_address = f"{reviewer[0]}.{reviewer[1]}@jumpcloud.com"
    reviewer_entry.languages = [LANGUAGES.get(l) for l in reviewer[2]]
db.session.commit()

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
    language_id = request.args.get("language")
    language_id = None if language_id in ("0", "None", None) else int(language_id)

    sort_key = request.args.get("sort") or "last_name"
    order = request.args.get("order") or "asc"

    reviewers = Reviewer.query.outerjoin(
        ReviewRequest, Reviewer.id == ReviewRequest.reviewer_id
    ).add_columns(
        Reviewer.id.label("id"),
        Reviewer.first_name.label("first_name"),
        Reviewer.last_name.label("last_name"),
        func.count(ReviewRequest.id).label("review_count"),
        func.max(ReviewRequest.review_date).label("last_review")
    ).group_by(
        Reviewer.id, Reviewer.first_name, Reviewer.last_name
    )
    if language_id:
        reviewers = reviewers.filter(
            Reviewer.languages.any(ReviewLanguage.id == language_id)
        )
    sorting = {"asc": asc, "desc": desc}[order]
    reviewers = reviewers.order_by(sorting(sort_key)).all()

    return render_template(
        "reviewers.html",
        reviewers=reviewers,
        languages=ReviewLanguage.query.all(),
        language_id=language_id,
        sort=sort_key,
        order=order,
    )


@app.route("/submit", methods=["POST"])
def open_mail():
    assignees = list(map(int, request.form.getlist("check")))
    language_id = request.form.get("language")
    print(language_id)
    language_id = None if language_id in ("0", "None", None) else int(language_id)
    print(assignees, language_id)
    if not assignees or not language_id:
        abort(400)
    reviewers = Reviewer.query.filter(Reviewer.id.in_(assignees)).all()
    for reviewer in reviewers:
        request_entry = ReviewRequest(
            reviewer_id=reviewer.id, review_language_id=language_id
        )
        db.session.add(request_entry)
    db.session.commit()

    mails = [r.email_address for r in reviewers]

    return redirect(
        f"mailto:{','.join(mails)}?subject=New Coding Project Review Request"
    )


@app.route("/manage/<int:reviewer_id>")
def edit_reviewer(reviewer_id):
    """Edit a reviewer's details."""
    reviewer = Reviewer.query.filter(Reviewer.id == reviewer_id).first()
    if not reviewer:
        abort(404)
    return render_template(
        "edit_reviewer.html",
        reviewer=reviewer,
        languages=ReviewLanguage.query.all()
    )


@app.route("/manage/edit_reviewer/<int:reviewer_id>", methods=["POST"])
def update_reviewer(reviewer_id):
    """Push updated reviewer data to database."""
    reviewer = Reviewer.query.filter(Reviewer.id == reviewer_id).first()
    if not reviewer:
        abort(404)
    reviewer.first_name = request.form.get("first_name")
    reviewer.last_name = request.form.get("last_name")
    reviewer.email_address = (
        f"{reviewer.first_name}.{reviewer.last_name}@jumpcloud.com"
    )
    reviewer.languages = ReviewLanguage.query.filter(
        ReviewLanguage.id.in_(request.form.getlist("languages"))
    ).all()
    db.session.add(reviewer)
    db.session.commit()
    return redirect(url_for("main_page"))

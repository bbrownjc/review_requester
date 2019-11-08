from datetime import datetime
import os

from flask import abort, Blueprint, Flask, redirect, render_template, request, url_for
from flask_restplus import Api, Resource, fields, reqparse
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

#################
# API Endpoints #
#################


def save_changes(data):
    db.session.add(data)
    db.session.commit()


reviewers = api.namespace("reviewers", description="Reviewer Management")
_reviewer = api.model(
    "reviewer",
    {
        "first_name": fields.String(required=True, description="reviewer first name"),
        "last_name": fields.String(required=True, description="reviewer last name"),
        "email_address": fields.String(
            required=True, description="reviewer email address"
        ),
        "languages": fields.List(fields.String),
    },
)

_reviewer_request = reqparse.RequestParser(bundle_errors=True)
_reviewer_request.add_argument("languages", action="append")


@reviewers.route("/")
class ReviewerList(Resource):
    @reviewers.doc("list of registered reviewers")
    @reviewers.marshal_list_with(_reviewer, envelope="data")
    @reviewers.expect(_reviewer_request)
    def get(self):
        """List of reviewers."""
        data = request.json
        query = Reviewer.query
        if len(data["languages"]) > 0:
            # TODO: Check other queries
            languages = [LANGUAGES.get(l) for l in data["languages"]]
            for l in languages:
                query = query.filter(Reviewer.languages.contains(l))
        # TODO: Add sort by
        return query.all()

    @reviewers.response(201, "Reviewer successfully created.")
    @reviewers.doc("create a new reviewer")
    @reviewers.expect(_reviewer, validate=True)
    def post(self):
        """Add a reviewer."""
        data = request.json
        reviewer_entry = Reviewer.query.filter_by(
            email_address=data["email_address"]
        ).first()
        if not reviewer_entry:
            languages = [LANGUAGES.get(l) for l in data["languages"]]
            new_reviewer = Reviewer(
                first_name=data["first_name"],
                last_name=data["last_name"],
                email_address=data["email_address"],
                languages=languages,
            )
            save_changes(new_reviewer)
            response_object = {
                "status": "success",
                "message": "Successfully registered.",
            }
            return response_object, 201
        else:
            response_object = {"status": "fail", "message": "Reviewer already exists."}
            return response_object, 409


@reviewers.route("/<int:id>")
@reviewers.param("id", "The Reviewer identifier")
@reviewers.response(404, "Reviewer not found.")
class ReviewerManagment(Resource):
    @reviewers.doc("get a reviewer")
    @reviewers.marshal_with(_reviewer)
    def get(self, id):
        """Retrieve a single reviewer."""
        reviewer = Reviewer.query.filter_by(id=id).first()
        if not reviewer:
            reviewers.abort(404)
        else:
            return reviewer

    @reviewers.response(200, "Reviewer successfully updated.")
    @reviewers.doc("updates a reviewer")
    @reviewers.expect(_reviewer, validate=True)
    def put(self, id):
        """Update a reviewer."""
        data = request.json
        reviewer = Reviewer.query.filter_by(id=id).first()
        reviewer.first_name = data["first_name"]
        reviewer.last_name = data["last_name"]
        reviewer.email_address = data["email_address"]
        reviewer.languages = languages
        db.session.commit()

    @reviewers.response(200, "Reviewer successfully deleted.")
    @reviewers.doc("removes a reviewer")
    def delete(self, id):
        """Remove a reviewer."""
        reviewer = Reviewer.query.filter_by(id=id).first()
        db.session.delete(reviewer)
        db.session.commit()


reviews = api.namespace("reviews", description="Review Request Data")
_review = api.model(
    "review",
    {
        "reviewer_id": fields.Integer(required=True, description="reviewer id"),
        "review_language_id": fields.Integer(required=True, description="language id"),
        "review_date": fields.Date(required=True, description="review date"),
    },
)


@reviews.route("/")
class Reviews(Resource):
    @reviews.doc("list of registered reviews")
    @reviews.marshal_list_with(_review, envelope="data")
    def get(self):
        """List of reviews."""
        return ReviewRequest.query.all()

    @reviews.response(201, "Review successfully created.")
    @reviews.doc("create a new review")
    @reviews.expect(_review, validate=True)
    def post(self):
        """Add a review."""
        data = request.json
        new_review = ReviewRequest(
            reviewer_id=data["reviewer_id"],
            review_language_id=data["review_language_id"],
            review_date=data["review_date"],
        )
        save_changes(new_review)
        response_object = {"status": "success", "message": "Successfully registered."}
        return response_object, 201


languages = api.namespace("languages", description="Language management")
_language = api.model(
    "language", {"name": fields.String(required=True, description="language name")}
)


@languages.route("/")
class Languages(Resource):
    @languages.doc("list of registered languages")
    @languages.marshal_list_with(_language, envelope="data")
    def get(self):
        """List of languages."""
        return ReviewLanguage.query.all()

    @languages.response(201, "Language successfully created.")
    @languages.doc("create a new language")
    @languages.expect(_language, validate=True)
    def post(self):
        """Add a language."""
        data = request.json
        new_language = ReviewLanguage(name=data["name"])
        save_changes(new_language)
        response_object = {"status": "success", "message": "Successfully registered."}
        return response_object, 201


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

    reviewers = (
        Reviewer.query.outerjoin(
            ReviewRequest, Reviewer.id == ReviewRequest.reviewer_id
        )
        .add_columns(
            Reviewer.id.label("id"),
            Reviewer.first_name.label("first_name"),
            Reviewer.last_name.label("last_name"),
            func.count(ReviewRequest.id).label("review_count"),
            func.max(ReviewRequest.review_date).label("last_review"),
        )
        .group_by(Reviewer.id, Reviewer.first_name, Reviewer.last_name)
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
        "edit_reviewer.html", reviewer=reviewer, languages=ReviewLanguage.query.all()
    )


@app.route("/manage/edit_reviewer/<int:reviewer_id>", methods=["POST"])
def update_reviewer(reviewer_id):
    """Push updated reviewer data to database."""
    reviewer = Reviewer.query.filter(Reviewer.id == reviewer_id).first()
    if not reviewer:
        abort(404)
    reviewer.first_name = request.form.get("first_name")
    reviewer.last_name = request.form.get("last_name")
    reviewer.email_address = f"{reviewer.first_name}.{reviewer.last_name}@jumpcloud.com"
    reviewer.languages = ReviewLanguage.query.filter(
        ReviewLanguage.id.in_(request.form.getlist("languages"))
    ).all()
    db.session.commit()
    return redirect(url_for("main_page"))


@app.route("/manage/delete_reviewer/<int:reviewer_id>")
def delete_reviewer(reviewer_id):
    reviewer = Reviewer.query.filter(Reviewer.id == reviewer_id).first()
    if not reviewer:
        abort(404)
    db.session.delete(reviewer)
    db.session.commit()
    return redirect(url_for("main_page"))


@app.route("/manage/add_reviewer")
def add_reviewer():
    """Edit a reviewer's details."""
    return render_template("add_reviewer.html", languages=ReviewLanguage.query.all())


@app.route("/manage/do_add", methods=["POST"])
def do_add_reviewer():
    """Push updated reviewer data to database."""
    reviewer = Reviewer()
    reviewer.first_name = request.form.get("first_name")
    reviewer.last_name = request.form.get("last_name")
    reviewer.email_address = f"{reviewer.first_name}.{reviewer.last_name}@jumpcloud.com"
    reviewer.languages = ReviewLanguage.query.filter(
        ReviewLanguage.id.in_(request.form.getlist("languages"))
    ).all()
    db.session.add(reviewer)
    db.session.commit()


@app.route("/leaderboard/reviewer_history/<int:reviewer_id>")
def reviewer_history(reviewer_id):
    reviewer = Reviewer.query.filter(Reviewer.id == reviewer_id).first()
    if not reviewer:
        abort(404)
    history = (
        ReviewRequest.query.join(
            ReviewLanguage, ReviewRequest.review_language_id == ReviewLanguage.id
        )
        .add_columns(
            ReviewRequest.review_date.label("date"),
            ReviewLanguage.name.label("language"),
        )
        .filter(ReviewRequest.reviewer_id == reviewer.id)
        .order_by(desc(ReviewRequest.review_date))
        .all()
    )
    return render_template("reviewer_history.html", reviewer=reviewer, history=history)


@app.route("/leaderboard/language_totals")
def language_metrics():
    totals = (
        ReviewLanguage.query.join(
            ReviewRequest, ReviewLanguage.id == ReviewRequest.review_language_id
        )
        .add_columns(
            ReviewLanguage.id.label("id"),
            ReviewLanguage.name.label("language"),
            func.count(ReviewRequest.id).label("review_count"),
        )
        .group_by(ReviewLanguage.id)
        .order_by(desc("review_count"))
        .all()
    )
    return render_template("language_totals.html", totals=totals)


@app.route("/leaderboard/language_history/<int:language_id>")
def language_history(language_id):
    language = ReviewLanguage.query.filter(
        ReviewLanguage.id == language_id
    ).first_or_404()
    history = (
        ReviewRequest.query.join(Reviewer, ReviewRequest.reviewer_id == Reviewer.id)
        .add_columns(
            ReviewRequest.review_date.label("review_date"),
            Reviewer.first_name.label("first_name"),
            Reviewer.last_name.label("last_name"),
        )
        .filter(ReviewRequest.review_language_id == language.id)
        .group_by(ReviewRequest.id, Reviewer.first_name, Reviewer.last_name)
        .order_by(desc(ReviewRequest.review_date))
        .all()
    )
    return render_template("language_history.html", language=language, history=history)

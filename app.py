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


<<<<<<< HEAD
=======
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

>>>>>>> upstream/master
#################
# API Endpoints #
#################

def save_changes(data):
    db.session.add(data)
    db.session.commit()

reviewers = api.namespace("reviewers", description="Reviewer Management")
# TODO: Add public fields
_reviewer =  api.model('reviewer', {})

@reviewers.route("/")
class ReviewerList(Resource):

    @reviewers.doc('list of registered reviewers')
    @reviewers.marshal_list_with(_reviewer, envelope='data')
    def get(self):
        """List of reviewers."""
        return Reviewer.query.all()

    @reviewers.response(201, 'Reviewer successfully created.')
    @reviewers.doc('create a new reviewer')
    @reviewers.expect(_reviewer, validate=True)
    def post(self):
        """Add a reviewer."""
        data = request.json
        # TODO: Validate new reviewer data
        new_reviewer = Reviewer()
        save_changes(new_reviewer)
        response_object = {
            'status': 'success',
            'message': 'Successfully registered.'
        }
        return response_object, 201


@reviewers.route("/<int:id>")
@reviewers.param('id', 'The Reviewer identifier')
@reviewers.response(404, 'Reviewer not found.')
class ReviewerManagment(Resource):

    @reviewers.doc('get a reviewer')
    @reviewers.marshal_with(_reviewer)
    def get(self, id):
        """Retrieve a single reviewer."""
        reviewer = Reviewer.query.filter_by(id=id).first()
        if not reviewer:
            reviewers.abort(404)
        else:
            return reviewer

    @reviewers.response(200, 'Reviewer successfully updated.')
    @reviewers.doc('updates a reviewer')
    @reviewers.expect(_reviewer, validate=True)
    def put(self, id):
        """Update a reviewer."""
        data = request.json
        # TODO: Validate new reviewer data
        new_reviewer = Reviewer()
        reviewer = Reviewer.query.filter_by(id=id).first()
        # TODO: Update fields
        db.session.commit()

    @reviews.response(200, 'Reviewer successfully deleted.')
    @reviewers.doc('removes a reviewer')
    def delete(self, id):
        """Remove a reviewer."""
        reviewer = Reviewer.query.filter_by(id=id).first()
        db.session.delete(reviewer)
        db.session.commit()


reviews = api.namespace("reviews", description="Review Request Data")
# TODO: Add public fields
_review = api.model('review', {})

@reviews.route("/")
class Reviews(Resource):

    @reviews.doc('list of registered reviews')
    @reviews.marshal_list_with(_review, envelope='data')
    def get(self):
        """List of reviews."""
        return Review.query.all()

    @reviews.response(201, 'Review successfully created.')
    @reviews.doc('create a new review')
    @reviews.expect(_review, validate=True)
    def post(self):
        """Add a review."""
        data = request.json
        # TODO: Validate new review data
        new_review = Review()
        save_changes(new_review)
        response_object = {
            'status': 'success',
            'message': 'Successfully registered.'
        }
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
    return render_template(
        "add_reviewer.html", languages=ReviewLanguage.query.all()
    )


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

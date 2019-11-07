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
    pass


@app.route("/manage")
def manage_reviewers():
    """Allow reviewer management."""
    pass


@app.route("/manage/<int:reviewer_id>")
def edit_reviewer(reviewer_id):
    """Edit a reviewer's details."""
    pass

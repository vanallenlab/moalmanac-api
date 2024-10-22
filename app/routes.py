import flask

from . import models


def create_response(data, message="", status=200):
    """Wrapper function to create a response with metadata."""
    response = {
        "status": status,
        "message": message,
        "data": data,
        "count": len(data)
    }
    return flask.jsonify(response), status


@flask.current_app.route('/test', methods=['GET'])
def test_route():
    return "Test route is working"


@flask.current_app.route('/about', methods=['GET'])
def get_about():
    session = models.Session()
    try:
        about = session.query(models.About).filter_by(id=0).first()
        if about:
            data = about.__dict__
            data.pop('_sa_instance_state', None)
            return create_response(
                data=data,
                message="About metadata retrieved successfully",
                status=200
            )
        else:
            return create_response(
                data={},
                message="No database metadata found",
                status=404
            )
    except Exception as e:
        print(f"Error occured: {e}")
        return create_response(
            data={"error": {e}},
            message="An error occured while retrieving about metadata",
            status=500
        )
    finally:
        session.close()

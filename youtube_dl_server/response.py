from flask import jsonify


class SuccessResponse:
    def __init__(self, payload=None):
        self.payload = payload

    def build(self):
        return jsonify({
            "success": True,
            "payload": self.payload
        })


class ErrorResponse:
    def __init__(self, message='An internal error occored.', code=400):
        self.message = message
        self.code = code

    def build(self):
        return jsonify({
            "success": False,
            "error": {
                "code": self.code,
                "message": self.message
            }
        })

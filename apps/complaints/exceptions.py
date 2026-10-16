from rest_framework import status
from rest_framework.exceptions import APIException


class ComplaintRuleViolation(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "This action is not allowed."
    default_code = "complaint_rule_violation"


class ComplaintConflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "There is already an open complaint for this booking."
    default_code = "complaint_conflict"
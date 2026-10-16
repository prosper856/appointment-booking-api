from rest_framework import status
from rest_framework.exceptions import APIException


class BookingConflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "This time slot is no longer available."
    default_code = "booking_conflict"


class BookingRuleViolation(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "This action is not allowed."
    default_code = "booking_rule_violation"
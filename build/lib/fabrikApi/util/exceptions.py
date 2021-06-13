# from http.client import HTTPException


# class AjaxException(HTTPException):

#     """
#     Is called when ajax request produces an exception
#     """

# # Use HTTPForbidden: pyramid.httpexceptions.HTTPForbidden
# # class AjaxForbidden(HTTPException):
# #
# #     """
# #     Is called when ajax request produces a forbidden error
# #     """
# #

# class AjaxRedirect(HTTPException):

#     """
#     Is called when ajax request produces a forbidden error
#     """
#     url = None

#     def __init__(self, url):
#         self.url = url


# class AjaxWarning(HTTPException):

#     """
#     Is called when ajax request shall return a warning or error message for the
#     user.
#     """

from django.shortcuts import get_object_or_404
from rest_framework import permissions


class IsEmailVerified(permissions.BasePermission):
    message = "Email verification is required to access this resource."

    def has_permission(self, request, view):
        # Check if the user is authenticated and their email is verified.
        return request.user.is_authenticated and request.user.email_verified

class IsOwner(permissions.BasePermission):
    message = "You are not the creator of this poll and do not have permission to access it."

    def has_object_permission(self, request, view, obj):
        # Check if the user is the creator of the election.
        return obj.created_by == request.user

class IsSuperUserOrObjectOwner(permissions.BasePermission):
    message = "Only object creator or superusers can access this resource."

    def has_object_permission(self, request, view, obj):
        # Check if the user is an election owner or a superuser.
        return any([
            obj.created_by == request.user,
            request.user.is_superuser
        ])

class AnonymousVoterPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        # Allow anonymous users with valid voter ID
        return 'X-Voter-Id' in request.headers


class IsAuthenticatedOrAnonymousVoter(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and 
            (request.user.is_authenticated or 
             getattr(request.user, 'is_anonymous_voter', False))
        )



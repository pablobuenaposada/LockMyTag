import datetime

from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from rest_framework import generics
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response

from api.locations.serializers import TagLocationRouteSerializer, TagLocationSerializer
from locations.models import Tag, TagLocation

ROUTE_MAX_POINTS = 10000


class TagLocationCreateView(generics.CreateAPIView):
    queryset = TagLocation.objects.all()
    serializer_class = TagLocationSerializer


class LatestTagLocationView(generics.GenericAPIView):
    serializer_class = TagLocationSerializer

    def get(self, request, tag_id):
        if not (
            latest_location := TagLocation.objects.filter(tag_id=tag_id)
            .order_by("-timestamp")
            .first()
        ):
            raise NotFound()
        return Response(self.get_serializer(latest_location).data)


class TagLocationRouteView(generics.GenericAPIView):
    serializer_class = TagLocationRouteSerializer

    @staticmethod
    def _parse_bound(value, param, end_of_day):
        """Accept either a date (2026-09-01) or a full datetime, return an aware one."""
        if not value:
            return None
        # Date-only first: parse_datetime() would happily read "2026-09-02" as
        # midnight, which would silently swallow the whole end day.
        if parsed_date := parse_date(value):
            time_of_day = datetime.time.max if end_of_day else datetime.time.min
            return timezone.make_aware(
                datetime.datetime.combine(parsed_date, time_of_day)
            )
        if not (parsed := parse_datetime(value)):
            raise ValidationError({param: "Must be a valid date or datetime."})
        return parsed if timezone.is_aware(parsed) else timezone.make_aware(parsed)

    def get(self, request, tag_id):
        if not Tag.objects.filter(id=tag_id).exists():
            raise NotFound()

        start = self._parse_bound(
            request.query_params.get("start"), "start", end_of_day=False
        )
        end = self._parse_bound(request.query_params.get("end"), "end", end_of_day=True)
        if start and end and start > end:
            raise ValidationError({"start": "Must not be after end."})

        locations = TagLocation.objects.filter(tag_id=tag_id)
        if start:
            locations = locations.filter(timestamp__gte=start)
        if end:
            locations = locations.filter(timestamp__lte=end)
        locations = locations.order_by("timestamp")

        # Fetch one extra to detect truncation without a second COUNT query
        points = list(locations[: ROUTE_MAX_POINTS + 1])
        truncated = len(points) > ROUTE_MAX_POINTS
        points = points[:ROUTE_MAX_POINTS]

        return Response(
            {
                "tag": tag_id,
                "count": len(points),
                "truncated": truncated,
                "points": self.get_serializer(points, many=True).data,
            }
        )

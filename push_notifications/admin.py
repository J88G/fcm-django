from django.apps import apps
from django.contrib import admin, messages
from django.utils.translation import ugettext_lazy as _
from .models import FCMDevice
from .settings import PUSH_NOTIFICATIONS_SETTINGS as SETTINGS
from .fcm import FCMError
User = apps.get_model(*SETTINGS["USER_MODEL"].split("."))


class DeviceAdmin(admin.ModelAdmin):
	list_display = ("__str__", "device_id", "user", "active", "date_created")
	list_filter = ("active",)
	actions = ("send_message", "send_bulk_message", "enable", "disable")
	raw_id_fields = ("user",)

	if hasattr(User, "USERNAME_FIELD"):
		search_fields = ("name", "device_id", "user__%s" % (User.USERNAME_FIELD))
	else:
		search_fields = ("name", "device_id")

	def send_messages(self, request, queryset, bulk=False):
		"""
		Provides error handling for DeviceAdmin send_message and send_bulk_message methods.
		"""
		ret = []
		errors = []
		r = ""

		for device in queryset:
			try:
				if bulk:
					r = queryset.send_message("Test notification", "Test bulk notification")
				else:
					r = device.send_message("Test notification", "Test single notification")
				if r:
					ret.append(r)
			except FCMError as e:
				errors.append(str(e))

			if bulk:
				break

		if errors:
			self.message_user(
				request, _("Some messages could not be processed: %r" % (", ".join(errors))),
				level=messages.ERROR
			)
		if ret:
			if not bulk:
				ret = ", ".join(ret)
			if errors:
				msg = _("Some messages were sent: %s" % (ret))
			else:
				msg = _("All messages were sent: %s" % (ret))
			self.message_user(request, msg)

	def send_message(self, request, queryset):
		self.send_messages(request, queryset)

	send_message.short_description = _("Send test message")

	def send_bulk_message(self, request, queryset):
		self.send_messages(request, queryset, True)

	send_bulk_message.short_description = _("Send test message in bulk")

	def enable(self, request, queryset):
		queryset.update(active=True)

	enable.short_description = _("Enable selected devices")

	def disable(self, request, queryset):
		queryset.update(active=False)

	disable.short_description = _("Disable selected devices")


admin.site.register(FCMDevice, DeviceAdmin)
# RentPe

## WhatsApp Rent Reminders

The backend now supports scheduled WhatsApp rent reminders using the WhatsApp Cloud API.

Set these backend environment variables before enabling it:

- `WHATSAPP_ENABLED=true`
- `WHATSAPP_PHONE_NUMBER_ID=...`
- `WHATSAPP_ACCESS_TOKEN=...`
- `WHATSAPP_TEMPLATE_NAME=...`
- `WHATSAPP_TEMPLATE_LANGUAGE=en`
- `WHATSAPP_DEFAULT_COUNTRY_CODE=91`
- `WHATSAPP_REMINDER_OFFSETS=3,1,0`
- `WHATSAPP_REMINDER_HOUR=9`
- `WHATSAPP_REMINDER_MINUTE=0`
- `APP_TIMEZONE=Asia/Kolkata`

The configured WhatsApp template must accept 5 body variables in this order:

1. Tenant name
2. Property name
3. Room number
4. Amount due
5. Due date

The backend runs a daily reminder job and records sends in `reminder_logs` to avoid re-sending the same reminder for the same room and due date. You can also trigger the current landlord's reminders manually with `POST /api/v1/billing/reminders/send` and an optional `property_id` query parameter.

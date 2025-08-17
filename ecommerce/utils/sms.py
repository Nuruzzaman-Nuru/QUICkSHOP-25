from flask import current_app

def send_sms(phone_number, message):
    """
    Send an SMS using Twilio (currently disabled for development)
    """
    # Skip SMS sending in development
    if not current_app.config.get('ENABLE_SMS', False):
        current_app.logger.info(f'SMS sending disabled. Would have sent to {phone_number}: {message}')
        return True
    try:
        account_sid = current_app.config['TWILIO_ACCOUNT_SID']
        auth_token = current_app.config['TWILIO_AUTH_TOKEN']
        from_number = current_app.config['TWILIO_PHONE_NUMBER']

        client = Client(account_sid, auth_token)
        message = client.messages.create(
            body=message,
            from_=from_number,
            to=phone_number
        )
        return True
    except Exception as e:
        current_app.logger.error(f'SMS sending failed: {str(e)}')
        return False

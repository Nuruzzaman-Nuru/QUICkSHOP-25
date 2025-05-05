from flask import current_app, render_template
from flask_mail import Message
from datetime import datetime, timedelta
from threading import Thread
from .. import mail, db
from ..models.user import User

def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

def send_email(subject, recipients, template, **kwargs):
    """
    Send an email using a template and keyword arguments.
    """
    app = current_app._get_current_object()
    msg = Message(
        subject=subject,
        recipients=recipients,
        html=render_template(template, **kwargs)
    )
    Thread(target=send_async_email, args=(app, msg)).start()

def notify_customer_order_status(order):
    """Send order status update notification to customer"""
    msg = Message(
        f'Order #{order.id} Status Update',
        recipients=[order.customer.email]
    )
    msg.html = render_template(
        'email/order_status_update.html',
        order=order
    )
    mail.send(msg)

def notify_shop_owner_new_order(order):
    """Notify shop owner about new orders"""
    msg = Message(
        f'New Order #{order.id} Received',
        recipients=[order.shop.owner.email]
    )
    msg.html = render_template(
        'email/new_order_notification.html',
        order=order
    )
    mail.send(msg)

def notify_admin_order_status(order, change=None):
    """Notify admin about order status changes"""
    admins = User.query.filter_by(role='admin').all()
    for admin in admins:
        msg = Message(
            f'Order #{order.id} Status Update',
            recipients=[admin.email]
        )
        msg.html = render_template(
            'email/admin_order_notification.html',
            order=order,
            change=change
        )
        mail.send(msg)

def notify_delivery_person_new_order(order):
    """Notify available delivery people about new deliverable orders"""
    delivery_persons = User.query.filter_by(
        role='delivery',
        is_active=True
    ).all()
    
    for person in delivery_persons:
        # Only notify if within reasonable distance
        if person.location_lat and person.location_lng:
            distance = calculate_distance(
                person.location_lat,
                person.location_lng,
                order.delivery_lat,
                order.delivery_lng
            )
            # Skip if more than 10km away
            if distance > 10:
                continue
        
        msg = Message(
            'New Delivery Order Available',
            recipients=[person.email]
        )
        msg.html = render_template(
            'email/new_order_available.html',
            order=order,
            delivery_person=person
        )
        mail.send(msg)

def notify_delivery_assignment(order, delivery_person):
    """Notify delivery person about being assigned to an order"""
    msg = Message(
        f'New Delivery Assignment - Order #{order.id}',
        recipients=[delivery_person.email]
    )
    msg.html = render_template(
        'email/delivery_assignment.html',
        order=order,
        delivery_person=delivery_person
    )
    mail.send(msg)

def notify_all_delivery_persons(message):
    """Send a notification message to all delivery persons"""
    delivery_persons = User.query.filter_by(role='delivery', is_active=True).all()
    
    for person in delivery_persons:
        msg = Message(
            'Delivery Service Update',
            recipients=[person.email]
        )
        msg.html = render_template(
            'email/general_notification.html',
            message=message,
            recipient=person
        )
        mail.send(msg)

def estimate_delivery_time(order):
    """Estimate delivery time in minutes based on distance and conditions"""
    if not (order.delivery_lat and order.delivery_lng and 
            order.shop.location_lat and order.shop.location_lng):
        return 60  # Default 1 hour if no coordinates
        
    # Calculate distance-based time
    distance = calculate_distance(
        order.shop.location_lat,
        order.shop.location_lng,
        order.delivery_lat,
        order.delivery_lng
    )
    
    # Base time calculation:
    # - 15 min base processing time
    # - 3 min per km distance
    # - Add 20% buffer for traffic/delays
    base_time = 15 + (distance * 3)
    base_time *= 1.2
    
    # Add time for multiple active deliveries
    if order.delivery_person:
        active_deliveries = Order.query.filter(
            Order.delivery_person_id == order.delivery_person_id,
            Order.status == 'delivering'
        ).count()
        if active_deliveries > 0:
            base_time += (active_deliveries * 10)  # Add 10 minutes per active delivery
    
    return round(base_time)
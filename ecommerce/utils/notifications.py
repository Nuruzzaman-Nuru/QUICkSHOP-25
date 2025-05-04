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
    """Notify customer about order status changes"""
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

def notify_all_delivery_persons(order):
    """Notify all available delivery persons about a new order"""
    delivery_persons = User.query.filter_by(
        role='delivery',
        is_active=True
    ).all()
    
    for person in delivery_persons:
        # Calculate distance between delivery person and shop
        from .distance import calculate_distance, estimate_travel_time
        distance = calculate_distance(
            person.location_lat,
            person.location_lng,
            order.shop.location_lat,
            order.shop.location_lng
        )
        
        # Only notify if within reasonable distance (e.g., 10km)
        if distance <= 10:
            send_email(
                'New Delivery Order Available',
                [person.email],
                'email/new_order_available.html',
                order=order,
                delivery_person=person,
                distance=distance,
                estimate_travel_time=estimate_travel_time
            )

def estimate_delivery_time(order):
    """
    Estimate delivery time in minutes based on:
    - Distance between shop and delivery address
    - Current traffic conditions (can be enhanced with external API)
    - Number of active deliveries for the assigned delivery person
    """
    if not order.delivery_lat or not order.delivery_lng:
        return 60  # Default 1 hour if no coordinates
        
    # Calculate base time using distance
    from .distance import calculate_distance
    distance = calculate_distance(
        order.shop.location_lat,
        order.shop.location_lng,
        order.delivery_lat,
        order.delivery_lng
    )
    
    # Base estimation: 3 minutes per kilometer plus 15 minutes fixed time
    base_time = (distance * 3) + 15
    
    # Add extra time for peak hours (between 11:00-14:00 and 18:00-21:00)
    current_hour = datetime.now().hour
    if (11 <= current_hour <= 14) or (18 <= current_hour <= 21):
        base_time *= 1.3
    
    # Add time for multiple active deliveries
    if order.delivery_person:
        active_deliveries = order.delivery_person.delivery_orders.filter(
            status='delivering'
        ).count()
        if active_deliveries > 0:
            base_time += (active_deliveries * 10)  # Add 10 minutes per active delivery
    
    return round(base_time)
import stripe
from flask import render_template, request, jsonify, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from app.donate import bp
from app.models import User


@bp.route('/<username>')
def donate_page(username):
    artist = User.query.filter_by(username=username).first_or_404()
    stripe_key = current_app.config.get('STRIPE_PUBLIC_KEY', '')
    return render_template('donate/index.html', title=f'Support {artist.username}',
                           artist=artist, stripe_key=stripe_key)


@bp.route('/create-payment-intent', methods=['POST'])
@login_required
def create_payment_intent():
    stripe.api_key = current_app.config.get('STRIPE_SECRET_KEY', '')
    if not stripe.api_key:
        return jsonify({'error': 'Payments not configured.'}), 400
    data = request.get_json()
    amount = int(data.get('amount', 500))
    try:
        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency='usd',
            automatic_payment_methods={'enabled': True},
        )
        return jsonify({'clientSecret': intent['client_secret']})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@bp.route('/create-subscription', methods=['POST'])
@login_required
def create_subscription():
    stripe.api_key = current_app.config.get('STRIPE_SECRET_KEY', '')
    if not stripe.api_key:
        return jsonify({'error': 'Payments not configured.'}), 400
    data = request.get_json()
    price_id = data.get('price_id')
    try:
        customer = stripe.Customer.create(email=current_user.email)
        subscription = stripe.Subscription.create(
            customer=customer['id'],
            items=[{'price': price_id}],
            payment_behavior='default_incomplete',
            expand=['latest_invoice.payment_intent'],
        )
        return jsonify({
            'subscriptionId': subscription['id'],
            'clientSecret': subscription['latest_invoice']['payment_intent']['client_secret']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

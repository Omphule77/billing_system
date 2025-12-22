from flask import Blueprint, render_template

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    return render_template('base.html')

@bp.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@bp.route('/bill')
def bill():
    return render_template('bill.html')

@bp.route('/create_bill')
def create_bill():
    return render_template('create_bill.html')

@bp.route('/add_item')
def add_item():
    return render_template('add_item.html')
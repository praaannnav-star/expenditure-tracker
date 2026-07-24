from flask import Flask, render_template, request, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "change_this_secret"

# DATABASE
uri = os.getenv(
    "DATABASE_URL",
    "postgresql://expenditure_m8yg_user:FM9WjjHXeg041D9GpAap9L51kRLasvIi@dpg-d6vouh9r0fns73ce1vh0-a.oregon-postgres.render.com/expenditure_m8yg"
)

if uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = uri
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# ================= MODELS =================

class UserData(db.Model):
    __tablename__ = "userdata"

    user_email_id = db.Column(db.String(200), primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(200), nullable=False)

    expenses = db.relationship('UserExpenditure', backref='user', lazy=True)


class UserExpenditure(db.Model):
    __tablename__ = "userexpenditure"

    expenseId = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    user_email_id = db.Column(db.String(200), db.ForeignKey('userdata.user_email_id'), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    expenseName = db.Column(db.String(200), nullable=False)


# ================= ROUTES =================

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/signup", methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get("username")
        email_id = request.form.get("emailId")
        password = generate_password_hash(request.form.get("password"))

        existing = UserData.query.filter_by(user_email_id=email_id).first()

        if existing:
            return render_template("signup.html", alert_message="User already exists")

        new_user = UserData(
            user_email_id=email_id,
            username=username,
            password=password
        )

        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for("login"))

    return render_template("signup.html")


@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get("username")
        password = request.form.get("password")

        user = UserData.query.filter_by(user_email_id=email).first()

        if user and check_password_hash(user.password, password):
            session['user'] = email
            return redirect(url_for("dashboard"))

        return render_template("login.html", alert_message="Invalid credentials")

    return render_template("login.html")


@app.route("/dashboard", methods=['GET', 'POST'])
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))

    user = UserData.query.filter_by(user_email_id=session['user']).first()

    if request.method == 'POST':
        expense = request.form.get("expense")
        amount = request.form.get("amount")
        date = request.form.get("date")

        new_expense = UserExpenditure(
            expenseName=expense,
            amount=int(amount),
            date=datetime.strptime(date, "%Y-%m-%d"),
            user_email_id=user.user_email_id
        )

        db.session.add(new_expense)
        db.session.commit()

        return redirect(url_for('dashboard'))

    expenses = user.expenses

    return render_template("dashboard.html", user=user, expenses=expenses)


@app.route("/logout")
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))


# ================= RUN =================

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)

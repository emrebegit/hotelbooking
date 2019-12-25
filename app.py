from flask import Flask,render_template,flash,redirect,url_for,request
from flask_wtf import FlaskForm
from wtforms import StringField,PasswordField,BooleanField,SubmitField
from wtforms.validators import InputRequired,Email,Length,EqualTo
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash,check_password_hash
from flask_login import LoginManager,UserMixin,login_user,login_required,logout_user,current_user
from datetime import datetime
from sqlalchemy import Date, cast,and_

app = Flask(__name__)

#Config
app.config['SECRET_KEY']='a random string'
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///database.db'
SQLALCHEMY_TRACK_MODIFICATIONS = False
db = SQLAlchemy(app)

#login initialize
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

#Tables
class User(UserMixin,db.Model):
    id = db.Column(db.Integer,primary_key=True)
    username = db.Column(db.String(),unique=True)
    email = db.Column(db.String())
    password = db.Column(db.String())
    reservations= db.relationship('Reservation',backref='user')
    bonus = db.Column(db.Integer)

class Room(db.Model):
    roomno = db.Column(db.Integer, primary_key=True)
    price = db.Column(db.Integer)
    capacity = db.Column(db.Integer)
    floorno = db.Column(db.Integer)
    childbed = db.Column(db.Integer)
    adultbed = db.Column(db.Integer)
    roomtype = db.Column(db.String(255))
    inDate = db.Column(db.Date)
    outDate=db.Column(db.Date)
    isreserve = db.Column('is_reserve',db.Boolean)
    reservations = db.relationship('Reservation',backref='room')
class Reservation(db.Model):
    invoiceno=db.Column(db.Integer,primary_key=True)
    time=db.Column(db.DateTime,index=True,default=datetime.now())
    totalamount=db.Column(db.Float)
    userid=db.Column(db.Integer,db.ForeignKey('user.id',ondelete='CASCADE'))
    roomno=db.Column(db.Integer,db.ForeignKey('room.roomno',ondelete='CASCADE'))  
class Baskets(db.Model):
    basketno=db.Column(db.Integer,primary_key=True)
    roomno=db.Column(db.Integer,db.ForeignKey('room.roomno',ondelete='CASCADE'))
    userid=db.Column(db.Integer,db.ForeignKey('user.id',ondelete='CASCADE'))
    price = db.Column(db.Integer)
    

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


db.create_all()


#Formlar
class LoginForm(FlaskForm):
    username = StringField('username',validators=[InputRequired()])
    password = PasswordField('password',validators=[InputRequired()])
    submit = SubmitField('Login')
class RegisterFrom(FlaskForm):
    username = StringField('username',validators=[InputRequired()])
    email = StringField('email',validators=[InputRequired(),Email()])
    password = PasswordField('password',validators=[InputRequired()])
    confirm_password = PasswordField('confirm_password',validators=[InputRequired(),EqualTo('password')])
    submit = SubmitField('Sign Up')

#Routes
@app.route('/')
def index():
    return render_template('index.html')
@app.route('/rooms',methods=['GET','POST'])
def rooms():
    if request.method == 'POST':
        
        indateold = str(request.form.get('indate'))
        indatesplited = indateold.split('/')
        month = indatesplited[0]
        day = indatesplited[1]
        year = indatesplited[2]
        count=len(day)
        if(count<2):
            indate = str(year+'-'+month+'-0'+day)
        else:
            indate = str(year+'-'+month+'-'+day)
   
        outdateold = str(request.form.get('outdate'))
        outdatesplited = outdateold.split('/')
        count1=len(outdatesplited[1])
        if(count1<2):
            outdate= str(outdatesplited[2]+'-'+outdatesplited[0]+'-0'+outdatesplited[1])
        else:
            outdate= str(outdatesplited[2]+'-'+outdatesplited[0]+'-'+outdatesplited[1])

        roomtype = str(request.form.get('roomtype'))
        adultbed = int(request.form.get('customer'))
        print(roomtype)
        
        result = Room.query.filter(Room.roomtype==roomtype).filter(Room.isreserve==0).filter(Room.inDate<=indate).filter(Room.outDate>=outdate).all() #Çalışıyor!

        return render_template('rooms.html',result=result)
    if request.method == 'GET':
        return render_template('rooms.html')
    return render_template('rooms.html')
@app.route('/roomdetail')
def roomdetail():
    return render_template('roomdetail.html')
@app.route('/about')
@login_required
def about():
    return render_template('about.html')
@app.route('/contact')
def contact():
    return render_template('contact.html')
@app.route('/login',methods=['GET','POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if check_password_hash(user.password,form.password.data):
                login_user(user)
                flash(f'You logged {form.username.data}','success')
        else:
            flash('Invald passwrod or username','error')
        
    return render_template('login.html',form=form)
@app.route('/register',methods=['GET','POST'])
def register():
    form = RegisterFrom()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data,method='sha256')
        new_user = User(username=form.username.data,email=form.email.data,password =hashed_password,bonus=0)
        db.session.add(new_user)
        db.session.commit()
        flash(f'Account created for {form.username.data}','success')
    return render_template('register.html',form=form)

@app.route('/logout')
@login_required
def logout():
    Baskets.query.filter_by(userid=current_user.id).delete()
    db.session.commit()
    logout_user()
    return redirect(url_for('index'))


@app.route('/admin',methods=['GET','POST'])
@login_required
def admin():
    if request.method == 'POST':
        price = int(request.form.get('price'))
        capacity = int(request.form.get('capacity'))
        floorno = int(request.form.get('floorno'))
        childbed = int(request.form.get('childbed'))
        adultbed= int(request.form.get('adultbed'))
        roomtype = request.form.get('roomtype')
        inDate = datetime.strptime(request.form.get('inDate'),'%Y-%m-%d')
        outDate = datetime.strptime(request.form.get('outDate'),'%Y-%m-%d')
        isreserve = str(request.form.get('isreserve'))
        if isreserve == 'on':
            isreserve ='1'
        elif isreserve == 'None':
            isreserve = '0'
        room = Room(price=price,capacity=capacity,floorno=floorno,childbed=childbed,adultbed=adultbed,roomtype=roomtype,inDate=inDate,outDate=outDate,isreserve=int(isreserve))
        db.session.add(room)
        db.session.commit()
        
        
    return render_template('admin.html')

@app.route('/book/<roomno>/<price>',methods=['GET','POST'])
@login_required
def book(roomno,price):
    bas=Baskets(userid=current_user.id,roomno=roomno,price=price)
    db.session.add(bas)
    db.session.commit()
    return render_template('index.html')

@app.route('/listbasket')
@login_required
def listbasket():
    list=db.session.query(Baskets).filter_by(userid=current_user.id)
    return render_template('basket.html',list=list)


@app.route('/reservations')
@login_required
def reservations():
    result=db.session.query(Reservation).filter(Reservation.userid==current_user.id).all()
    return render_template('info.html',result=result)


@app.route('/insres/<roomno>/<basketno>')#sepetten rezervasyon ekleme
@login_required
def insres(roomno,basketno):
    room=Room.query.get(roomno)
    bas=Baskets.query.get(basketno)
    res=Reservation(userid=current_user.id,roomno=room.roomno,totalamount=bas.price)
    db.session.commit()
    db.session.add(res)
    addbonus=current_user.bonus
    addbonus+=room.price*0.03
    current_user.bonus=addbonus
    room=Room.query.get(roomno)
    room.isreserve=True
    Baskets.query.filter_by(basketno=basketno).delete()
    db.session.commit()
    return render_template('info.html')


@app.route('/insresdirect/<roomno>')
@login_required
def insresdirect(roomno):
    room=Room.query.get(roomno)
    res=Reservation(userid=current_user.id,roomno=room.roomno,totalamount=room.price)
    db.session.add(res)
    addbonus=current_user.bonus
    addbonus+=room.price*0.03
    current_user.bonus=addbonus
    room=Room.query.get(roomno)
    room.isreserve=True
    db.session.commit()
    return render_template('info.html')
    



@app.route('/delres/<invoiceno>/<roomno>')
@login_required
def delres(invoiceno,roomno):
    Reservation.query.filter_by(invoiceno=invoiceno).delete()
    room=Room.query.get(roomno)
    room.isreserve=False
    db.session.commit()
    return redirect(url_for('reservations'))


@app.route('/delbasket/<basketno>')
@login_required
def delbasket(basketno):
    Baskets.query.filter_by(basketno=basketno).delete()
    db.session.commit()
    return redirect(url_for('listbasket'))


@app.route('/adminlist')
@login_required
def adminList():
    rooms = Room.query.all()
    return render_template('admin-list.html',rooms=rooms)

@app.route('/deleteroom/<roomno>')
def deleteroom(roomno):
    Room.query.filter_by(roomno=roomno).delete()
    db.session.commit()
    return redirect(url_for('adminList'))
@app.route('/getupdateroom/<roomno>',methods=['GET','POST'])
def getupdateroom(roomno):
    if request.method=='GET':
        room = Room.query.filter_by(roomno=roomno).first()
        return render_template('updateroom.html',room=room)
@app.route('/updateroom/<roomno>',methods=['GET','POST'])
def updateroom(roomno):
    if request.method=='POST':
        room = Room.query.filter_by(roomno=roomno).first()
        room.capacity = int(request.form.get('capacity'))
        room.price = int(request.form.get('price'))
        room.floorno = int(request.form.get('floorno'))
        room.childbed = int(request.form.get('childbed'))
        room.adultbed = int(request.form.get('adultbed'))
        room.roomtype = request.form.get('roomtype')
        room.inDate = datetime.strptime(request.form.get('inDate'),'%Y-%m-%d')
        room.outDate = datetime.strptime(request.form.get('outDate'),'%Y-%m-%d')
        isreserve = str(request.form.get('isreserve'))
        if isreserve == 'on':
            isreserve =True
        elif isreserve == 'None':
            isreserve = False
        room.isreserve = isreserve
        db.session.commit()
        return redirect(url_for('adminList'))
    return redirect('admin-list.html')


@app.route('/usebonus/<basketno>/<price>')
@login_required
def usebonus(basketno,price):
    bas=Baskets.query.get(basketno)
    bas.price=bas.price-current_user.bonus
    current_user.bonus=0
    db.session.commit()
    return redirect(url_for('listbasket'))

@app.route('/rate1',methods=['GET','POST'])
def rate1():
    if request.method == 'POST':
        
        indateold = str(request.form.get('indate'))
        indatesplited = indateold.split('/')
        month = indatesplited[0]
        day = indatesplited[1]
        year = indatesplited[2]
        count=len(day)
        if(count<2):
            indate = str(year+'-'+month+'-0'+day)
        else:
            indate = str(year+'-'+month+'-'+day)
   
        outdateold = str(request.form.get('outdate'))
        outdatesplited = outdateold.split('/')
        count1=len(outdatesplited[1])
        if(count1<2):
            outdate= str(outdatesplited[2]+'-'+outdatesplited[0]+'-0'+outdatesplited[1])
        else:
            outdate= str(outdatesplited[2]+'-'+outdatesplited[0]+'-'+outdatesplited[1])
        
        
        
        result = Room.query.filter(Room.isreserve==0).filter(Room.inDate>=indate).filter(Room.outDate<=outdate).count()
        result1 = Room.query.filter(Room.isreserve==1).filter(Room.inDate>=indate).filter(Room.outDate<=outdate).count()
        sum=result1+result
        query=int((result1*100)/sum)
        return render_template('rate.html',query=query)

@app.route('/rate')
def rate():
    return render_template('rate.html')    
    
app.run(debug=True)
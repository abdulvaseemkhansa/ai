from flask import Blueprint, abort, g, session, request, render_template, json, url_for
from flask_cors import cross_origin
from werkzeug.utils import redirect
from collections import OrderedDict
import uuid
from csatai.model import Subscriptions,QueryResults, RegisteredEvaluationService, CompanyUser, \
    Configsettings,UserSession, Companies
import datetime
import psycopg2

mod = Blueprint('companyadminsite',__name__,template_folder='templates')

@mod.before_request
def before_request():
    if request.args is not None:
        retriveUserSessionData (request.args, request)
    elif request.json is not None:
        retriveUserSessionData (request.json, request)

@mod.route ('/logout', methods=['GET'])
def get_logout():
    if 'user' in session:
        session.pop ('user_id', None)

    deleteUserSession (request.args)

    return redirect ('/company/admin')

@mod.route ('/companyuserlogin', methods=['POST'])
@cross_origin ()
def get_companyUserLogin():
    loginResult = {}
    if 'usercode' in   request.json and 'password' in request.json :
        loginResult =  CompanyUser.login(request.json)
        if loginResult['pass'] == False :
            loginResult['error'] = 'Invalid user id and password.'
        else:
            loginResult['error'] = ''
            subscriptionFinalData=getCompanySubscribedEvaluationData (loginResult)
            loginResult['EVALUATION_SETTING']=subscriptionFinalData
        return json.dumps (loginResult)

def getCompanySubscribedEvaluationData(loginResult):
    evalutionJsonData=RegisteredEvaluationService.getCompanySubscribedCategoryBYid (loginResult['companyid'],
                                                                                            loginResult['channelid'])
    subscriptionFinalData={}
    for eachData in evalutionJsonData:
        subscriptionFinalData[evalutionJsonData[eachData]['sequenceorder']]=evalutionJsonData[eachData]

        subscriptionFinalData=json.dumps (subscriptionFinalData, sort_keys=True)

    return subscriptionFinalData

@mod.route ('/admin', methods=['GET','POST'])
def get_companyadmin():
    result=''   
    errorMsg=None
    if request.method == 'POST':
        session.pop ('user', None)
        if request.form['username'] != '' and request.form['password'] != '':
            result= CompanyUser.weblogin(request.form['username'], request.form['password'],1)
            if result == '' or result is None:
                errorMsg='Invalid User Name and Password, Please try again!'
            else:
                if result.role.upper() != "ADMIN":
                    errorMsg='Invalid User Name and Password, Please try again!'
                else:
                    isBlocked = False
                    company=Companies.getAllRegisteredCompanies (result.company_id)
                    if company is not None:
                        if (company.is_locked == 'Y'):
                            errorMsg='Please upgrade your subscription!'
                        else:
                            session['user']=request.form['username']
                            session['name']=result.user_name
                            session['user_id']=result.user_code
                            session['company_id']=result.company_id
                            session['enrole_to_service']=result.enrole_to_service
                            session['role']=result.role
                            sessionid=uuid.uuid4 ()
                            session['sessionid']=str (sessionid)
                            UserSession.createSessionData (session,request)

                            return redirect (url_for('companyadminsite.get_companyhome',sessionid=str(sessionid)),code=302)
        else:
            errorMsg='Invalid User Name and Password, Please try again!'

    return render_template ('clogin.html', error=errorMsg)


@mod.route ('/home', methods=['GET', 'POST'])

def get_companyhome():
    result=''
    errorMsg=None
    if 'company_id' in session:
        userlist=None
        subscriptionslist=None
        if session['role'].upper() == "ADMIN":
            userlist=CompanyUser.userlist (session['company_id'])
            subscriptionslist=Subscriptions.getCompanySubscriptionDetailsBYid (session['company_id'])

            Evaluationsubscriptionslist=RegisteredEvaluationService.getAllEvalSubscriptionDataBYCompany(session['company_id'])

            graphreport = getgraphData()
            legend = " Date"
            conn = psycopg2.connect("dbname='csataidb' user='postgres' host='localhost' password='navedas'")
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT date from daily_stats")
                # data = cursor.fetchone()
                rows = cursor.fetchall()
                labels = list()
                i = 0
                for row in rows:
                    labels.append(row[i])

                cursor.execute("SELECT TO_CHAR(now() :: DATE, 'dd/mm/yyyy');")
                # data = cursor.fetchone()
                rows = cursor.fetchall()
                labels1 = list()
                i = 0
                for row in rows:
                    labels1.append(row[i])

                cursor.execute("SELECT TO_CHAR(now()::DATE, 'dd/mm/yyyy')FROM   GENERATE_SERIES(1, 2)")
                # data = cursor.fetchone()
                rows = cursor.fetchall()
                labels2 = list()
                i = 0
                for row in rows:
                    labels2.append(row[i])

                cursor.execute("select TO_CHAR(now()::DATE-interval '1day', 'dd/mm/yyyy')")
                # data = cursor.fetchone()
                rows = cursor.fetchall()
                labels3 = list()
                i = 0
                for row in rows:
                    labels3.append(row[i])

                cursor.execute("select TO_CHAR(i :: DATE, 'dd/mm/yyyy') from generate_series(current_date - interval '6 day',  current_date , '1 day'::interval) i ")
                # data = cursor.fetchone()
                rows = cursor.fetchall()
                labels4 = list()
                i = 0
                for row in rows:
                    labels4.append(row[i])

                cursor.execute(
                    "select TO_CHAR(i :: DATE, 'dd/mm/yyyy') from generate_series(current_date - interval '29 day',  current_date , '1 day'::interval) i ")
                # data = cursor.fetchone()
                rows = cursor.fetchall()
                labels5 = list()
                i = 0
                for row in rows:
                    labels5.append(row[i])

                cursor.execute("select TO_CHAR(i :: DATE, 'dd/mm/yyyy') from generate_series(date_trunc('month', current_date),  current_date, '1 day'::interval) i  ")
                # data = cursor.fetchone()
                rows = cursor.fetchall()
                labels6 = list()
                i = 0
                for row in rows:
                    labels6.append(row[i])

                cursor.execute("select score*100 from daily_stats1 where  user_id=102")
                rows = cursor.fetchall()[:len(labels6)]
                # Convert query to objects of key-value pairs
                presentmonth1 = list()
                i = 0
                for row in rows:
                    presentmonth1.append(row[i])


                cursor.execute("select i::date from generate_series(current_date - interval '365 day',  current_date , '1 day'::interval) i")
                # data = cursor.fetchone()
                rows = cursor.fetchall()
                custom_labels = list()
                i = 0
                for row in rows:
                    custom_labels.append(row[i])

                cursor.execute(
                    "select TO_CHAR(i :: DATE, 'dd/mm/yyyy') from generate_series(date_trunc('month', current_date - interval '1 month'),  date_trunc('month', current_date )-interval '1 day', '1 day'::interval) i  ")
                # data = cursor.fetchone()
                rows = cursor.fetchall()
                labels7 = list()
                i = 0
                for row in rows:
                    labels7.append(row[i])

                cursor.execute("select TO_CHAR(date :: DATE, 'dd/mm/yyyy') from daily_stats1 where user_id=101")
                # data = cursor.fetchone()
                rows = cursor.fetchall()
                query_labels = list()
                i = 0
                for row in rows:
                    query_labels.append(row[i])

                cursor.execute("select round(avg(no_of_interactions)) from daily_stats1 group by user_id;")
                rows = cursor.fetchall()
                # Convert query to objects of key-value pairs
                values = list()
                i = 0
                for row in rows:
                    values.append(row[i])

                cursor.execute("SELECT score*100 from daily_stats1 where user_id='102'")
                rows = cursor.fetchall()
                # Convert query to objects of key-value pairs
                values1 = list()
                i = 0
                for row in rows:
                    values1.append(row[i])

                cursor.execute("SELECT no_of_interactions from daily_stats1 where user_id='101'")
                rows = cursor.fetchall()
                # Convert query to objects of key-value pairs
                values2 = list()
                i = 0
                for row in rows:
                    values2.append(row[i])

                cursor.execute("select round(avg(score*100)) from daily_stats1 group by user_id;")
                rows = cursor.fetchall()
                # Convert query to objects of key-value pairs
                values3 = list()
                i = 0
                for row in rows:
                    values3.append(row[i])

                cursor.execute("select score*100 from daily_stats1 where id between 1 and 30")
                rows = cursor.fetchall()
                # Convert query to objects of key-value pairs
                values4 = list()
                i = 0
                for row in rows:
                    values4.append(row[i])

                cursor.execute("select score*100 from daily_stats1 where id between 20 and 49")
                rows = cursor.fetchall()
                # Convert query to objects of key-value pairs
                values5 = list()
                i = 0
                for row in rows:
                    values5.append(row[i])

                cursor.execute("select score*100 from daily_stats1 where id between 30 and 58")
                rows = cursor.fetchall()
                # Convert query to objects of key-value pairs
                values6 = list()
                i = 0
                for row in rows:
                    values6.append(row[i])

                cursor.execute("select score*100 from daily_stats1 where id between 10 and 39")
                rows = cursor.fetchall()
                # Convert query to objects of key-value pairs
                values7 = list()
                i = 0
                for row in rows:
                    values7.append(row[i])

                cursor.execute("select avg(score*100)from daily_stats1 where date=date group by date")
                rows = cursor.fetchall()
                # Convert query to objects of key-value pairs
                query_values = list()
                i = 0
                for row in rows[:30]:
                    query_values.append(row[i])

                cursor.execute("select avg(score*100)from daily_stats1 where date=date group by date")
                rows = cursor.fetchall()
                # Convert query to objects of key-value pairs
                quer_values = list()
                i = 0
                for row in rows[:30]:
                    quer_values.append(row[i])

                cursor.execute("select avg(no_of_interactions)from daily_stats1 where date=date group by date")
                rows = cursor.fetchall()
                # Convert query to objects of key-value pairs
                query_values1 = list()
                i = 0
                for row in rows:
                    query_values1.append(row[i])

                cursor.execute(
                    "select score*100 from daily_stats1 where  user_id=102 ")
                rows = cursor.fetchall()
                # Convert query to objects of key-value pairs
                query_values2 = list()
                i = 0
                for row in rows:
                    query_values2.append(row[i])

                cursor.execute(
                    "select score*100 from daily_stats1 where user_id=101 ")
                rows = cursor.fetchall()
                # Convert query to objects of key-value pairs
                query_values3 = list()
                i = 0
                for row in rows:
                    query_values3.append(row[i])

                    cursor.execute("SELECT floor(random() * (95-40+1) + 40)::int from generate_series(1,365)")
                    rows = cursor.fetchall()
                    # Convert query to objects of key-value pairs
                    custom_values = list()
                    i = 0
                    for row in rows:
                        custom_values.append(row[i])

                        cursor.execute("select current_date - interval '4days'")
                        rows = cursor.fetchall()
                        # Convert query to objects of key-value pairs
                        custom_values1= list()
                        i = 0
                        for row in rows:
                            custom_values1.append(row[i])

                cursor.execute("select current_date - interval '2days'")
                rows = cursor.fetchall()
                # Convert query to objects of key-value pairs
                custom_values2 = list()
                i = 0
                for row in rows:
                    custom_values2.append(row[i])


                cursor.execute("SELECT user_name from daily_stats where id=8")
                rows = cursor.fetchall()
                # Convert query to objects of key-value pairs
                user1 = list()
                i = 0
                for row in rows:
                    user1.append(row[i])

                cursor.execute("SELECT user_name from daily_stats where id=1")
                rows = cursor.fetchall()
                # Convert query to objects of key-value pairs
                user2 = list()
                i = 0
                for row in rows:
                    user2.append(row[i])

                cursor.execute("select avg(no_of_interactions) from daily_stats1 where id=1 or id=32")
                rows = cursor.fetchall()
                # Convert query to objects of key-value pairs
                random_today = list()
                i = 0
                for row in rows:
                    random_today.append(row[i])


                cursor.execute("select score*100 from daily_stats1 where id=10")
                rows = cursor.fetchall()
                # Convert query to objects of key-value pairs
                random_today1 = list()
                i = 0
                for row in rows:
                    random_today1.append(row[i])

                cursor.execute("select score*100 from daily_stats1 where id=11")
                rows = cursor.fetchall()
                # Convert query to objects of key-value pairs
                random_today2 = list()
                i = 0
                for row in rows:
                    random_today2.append(row[i])

                cursor.execute("select avg(score*100)from daily_stats1 where id=10 or id=11")
                rows = cursor.fetchall()
                # Convert query to objects of key-value pairs
                random_today3 = list()
                i = 0
                for row in rows:
                    random_today3.append(row[i])

                cursor.execute("select avg(no_of_interactions) from daily_stats1 where id=7 or id=40")
                rows = cursor.fetchall()
                # Convert query to objects of key-value pairs
                yesterday = list()
                i = 0
                for row in rows:
                    yesterday.append(row[i])

                cursor.execute("select score*100 from daily_stats1 where id=39")
                rows = cursor.fetchall()
                # Convert query to objects of key-value pairs
                yesterday1 = list()
                i = 0
                for row in rows:
                    yesterday1.append(row[i])

                cursor.execute("select score*100 from daily_stats1 where id=6")
                rows = cursor.fetchall()
                # Convert query to objects of key-value pairs
                yesterday2 = list()
                i = 0
                for row in rows:
                    yesterday2.append(row[i])

                cursor.execute("select avg(score*100) from daily_stats1 where id=6 or id=39")
                rows = cursor.fetchall()
                # Convert query to objects of key-value pairs
                yesterday3 = list()
                i = 0
                for row in rows:
                    yesterday3.append(row[i])

                cursor.execute(
                    "select no_of_interactions from daily_stats1 where score*100 between 50 and 60 and user_id=101")
                rows = cursor.fetchall()
                # Convert query to objects of key-value pairs
                query_resolved = list()
                i = 0
                for row in rows:
                    query_resolved.append(row[i])

                cursor.execute(
                    "select score*100 from daily_stats1 where score*100 between 50 and 60 and user_id=102")
                rows = cursor.fetchall()
                # Convert query to objects of key-value pairs
                query_resolved1 = list()
                i = 0
                for row in rows:
                    query_resolved1.append(row[i])


                cursor.execute("select score*100 from daily_stats1 where score*100 between 50 and 60 and user_id=101")
                rows = cursor.fetchall()
                # Convert query to objects of key-value pairs
                query_resolved2 = list()
                i = 0
                for row in rows:
                    query_resolved2.append(row[i])

                cursor.execute(
                    "select date from daily_stats1 where score*100 between 50 and 60 and user_id=101")
                rows = cursor.fetchall()
                # Convert query to objects of key-value pairs
                query_resolved_labels = list()
                i = 0
                for row in rows:
                    query_resolved_labels.append(row[i])

                cursor.execute("select no_of_interactions from daily_stats1 where score*100 between 60 and 70 and user_id=101")
                rows = cursor.fetchall()
                # Convert query to objects of key-value pairs
                empathy = list()
                i = 0
                for row in rows:
                    empathy.append(row[i])

                cursor.execute("select score*100 from daily_stats1 where score*100 between 60 and 70 and user_id=102")
                rows = cursor.fetchall()
                # Convert query to objects of key-value pairs
                empathy1 = list()
                i = 0
                for row in rows:
                    empathy1.append(row[i])

                cursor.execute("select score*100 from daily_stats1 where score*100 between 60 and 70 and user_id=101")
                rows = cursor.fetchall()
                # Convert query to objects of key-value pairs
                empathy2 = list()
                i = 0
                for row in rows:
                    empathy2.append(row[i])

                cursor.execute(
                    "select date from daily_stats1 where score*100 between 60 and 70 and user_id=101")
                rows = cursor.fetchall()
                # Convert query to objects of key-value pairs
                empathy_labels = list()
                i = 0
                for row in rows:
                    empathy_labels.append(row[i])

                cursor.execute(
                    "select no_of_interactions from daily_stats1 where score*100>70 and user_id=102")
                rows = cursor.fetchall()
                # Convert query to objects of key-value pairs
                wow = list()
                i = 0
                for row in rows:
                    wow.append(row[i])


                cursor.execute(
                    "select score*100 from daily_stats1 where score*100>70 and user_id=102")
                rows = cursor.fetchall()
                # Convert query to objects of key-value pairs
                wow1 = list()
                i = 0
                for row in rows:
                    wow1.append(row[i])

                cursor.execute(
                    "select score*100 from daily_stats1 where score*100>70 and user_id=101")
                rows = cursor.fetchall()
                # Convert query to objects of key-value pairs
                wow2 = list()
                i = 0
                for row in rows:
                    wow2.append(row[i])

                cursor.execute(
                    "select date from daily_stats1 where score*100>70 and user_id=102")
                rows = cursor.fetchall()
                # Convert query to objects of key-value pairs
                wow_labels = list()
                i = 0
                for row in rows:
                    wow_labels.append(row[i])

                cursor.execute("select score*100 from daily_stats1 where  user_id=102")
                rows = cursor.fetchall()
                # Convert query to objects of key-value pairs
                lastweek1 = list()
                i = 0
                for row in rows[:7]:
                    lastweek1.append(row[i])

                cursor.execute("select score*100 from daily_stats1 where user_id=101")
                rows = cursor.fetchall()
                # Convert query to objects of key-value pairs
                lastweek2 = list()
                i = 0
                for row in rows[:7]:
                    lastweek2.append(row[i])

                cursor.execute("select avg(score*100)from daily_stats1 where date=date group by date")
                rows = cursor.fetchall()
                # Convert query to objects of key-value pairs
                lastweek3 = list()
                i = 0
                for row in rows[:7]:
                    lastweek3.append(row[i])

                cursor.execute("select score*100 from daily_stats1 where  user_id=102")
                rows = cursor.fetchall()
                # Convert query to objects of key-value pairs
                last30days1 = list()
                i = 0
                for row in rows[:30]:
                    last30days1.append(row[i])

                cursor.execute("select score*100 from daily_stats1 where  user_id=101")
                rows = cursor.fetchall()
                # Convert query to objects of key-value pairs
                last30days2 = list()
                i = 0
                for row in rows[:30]:
                    last30days2.append(row[i])

                cursor.execute("select avg(score*100)from daily_stats1 where date=date group by date")
                rows = cursor.fetchall()
                # Convert query to objects of key-value pairs
                last30days3 = list()
                i = 0
                for row in rows[:30]:
                    last30days3.append(row[i])



                cursor.execute("select score*100 from daily_stats1 where  user_id=101")
                rows = cursor.fetchall()[:len(labels6)]
                # Convert query to objects of key-value pairs
                presentmonth2 = list()
                i = 0
                for row in rows:
                    presentmonth2.append(row[i])

                cursor.execute("select avg(score*100)from daily_stats1 where date=date group by date")
                rows = cursor.fetchall()[:len(labels6)]
                # Convert query to objects of key-value pairs
                presentmonth3 = list()
                i = 0
                for row in rows:
                    presentmonth3.append(row[i])

                cursor.close()
                conn.close()


            except:
                print
                "Error: unable to fetch items"

            return render_template ('home.html', logininfo=session, userlist=userlist, graphreport=graphreport,
                                        subscriptionslist=subscriptionslist,evaluationsubscriptionslist=Evaluationsubscriptionslist,session=session
                                    , values=values, labels=labels, legend=legend,user1=user1,user2=user2,values1=values1,values2=values2,labels1=labels1,labels2=labels2,
                                   labels3=labels3,labels4=labels4,labels5=labels5 ,labels6=labels6,labels7=labels7,values3=values3,values4=values4,values5=values5,values6=values6,
                                    values7=values7,query_values=query_values,query_values1=query_values1,query_labels=query_labels,query_values2=query_values2,query_values3=query_values3,
                                    random_today=random_today,random_today1=random_today1,random_today2=random_today2,random_today3=random_today3,quer_values=quer_values,
                                    query_resolved2=query_resolved2,query_resolved1=query_resolved1,empathy1=empathy1,empathy2=empathy2,wow1=wow1,wow2=wow2,
                                    query_resolved=query_resolved,query_resolved_labels=query_resolved_labels,empathy=empathy,empathy_labels=empathy_labels,wow=wow,
                                    wow_labels=wow_labels,lastweek1=lastweek1,lastweek2=lastweek2,lastweek3=lastweek3,last30days1=last30days1,last30days2=last30days2,
                                    last30days3=last30days3,yesterday=yesterday,yesterday3=yesterday3,yesterday1=yesterday1,yesterday2=yesterday2,presentmonth1=presentmonth1,
                                    presentmonth2=presentmonth2,presentmonth3=presentmonth3,custom_labels=custom_labels,custom_values=custom_values,custom_values1=custom_values1,
                                    custom_values2=custom_values2,)
        else:
            errorMsg='Invalid User ID and Password, Please try again.'
            session.pop ('user', None)
            return render_template ('clogin.html', error=errorMsg)

        return redirect ('/company/admin')


@mod.route ('/userlist', methods=['GET'])
def get_userlist():
    if 'company_id' in session:
        result=''
        errorMsg=None
        userlist = None
        userlist = CompanyUser.userlist(session['company_id'])
        subscriptionslist = Subscriptions.getCompanySubscriptionDetailsBYid(session['company_id'])
        subscriptionsAssociativearray = {}
    
        for subscription in subscriptionslist:
            key = subscription.channel_id
            value = subscription.channel_name
            subscriptionsAssociativearray[key] = value

        return render_template ('companyuser.html', error=errorMsg,userlist=userlist,subscriptionsAssociativearray=subscriptionsAssociativearray,session=session)

    return redirect ('/company/admin')

@mod.route ('/adduser', methods=['GET','POST'])
def get_company():
    if 'company_id' in session:
        if request.method == 'POST':
            userid = request.form['userid']
            user_code = request.form['usercode']
            user_name = request.form['username']
            login_id = request.form['loginid']
            user_key = request.form['password']
            role = request.form['role']
            company_id = session['company_id']
            enrole_to_service = request.form['permission']
            is_active = request.form['isactive']

            CompanyUser.saveUserData(userid,user_code,user_name,login_id,user_key,role,company_id,enrole_to_service,is_active)
            return redirect(url_for('companyadminsite.get_userlist',session=session),code=302)

    return redirect ('/company/admin')

@mod.route ('/userpasswordreset', methods=['POST'])
def deleteUserData():
    if 'company_id' in session:
        if request.method == 'POST':
            userid = request.form['userid']
            returnVal = CompanyUser.resetUserPassword(userid,session['company_id'])
            result = {}
            result['status']="success"
            return json.dumps(result)

    return redirect ('/company/admin')

@mod.route ('/setting/<int:channel>', methods=['GET'])
def get_configSettingData(channel):
    if 'company_id' in session:
        channelid = channel
        subscriptiondata = RegisteredEvaluationService.getCompanySubscribedCategoryBYid(session['company_id'], channel)
        confgsettingdata = Configsettings.getConfigSettingById(session['company_id'],channel)

        subscriptionFinalData = {}
        for eachData in subscriptiondata:
            subscriptionFinalData[subscriptiondata[eachData]['sequenceorder']]=subscriptiondata[eachData]

        subscriptiondata = json.dumps(subscriptionFinalData,sort_keys=True)
        result = {}
        result['subscriptiondata']=json.loads(subscriptiondata,object_pairs_hook=OrderedDict)
        result['settingdata']=json.loads(confgsettingdata)
        subscriptionslist = Subscriptions.getCompanySubscriptionDetailsBYid(session['company_id'])
        return render_template ('companyusersetting.html',selectchannel=channelid,subscriptionslist=subscriptionslist,result=result,session=session)
        #return json.dumps(result)
    return redirect ('/company/admin')

@mod.route ('/savesetting', methods=['GET','POST'])
def get_savesetting():
    result={}

    if 'company_id' in session:
        if request.method == 'POST':
            postvars = splitTableFormData(request.form)

            configData = {}
            if('anonymous_data' in postvars[0]):
                configData['ANONYMOUS_DATA_SAVE'] = True
            else:
                configData['ANONYMOUS_DATA_SAVE'] = False

            if ('enable_context_warning' in postvars[0]):
                configData['ENABLE_CONTEXT_WARMING'] = True
            else:
                configData['ENABLE_CONTEXT_WARMING'] = False

            if ('results_for_reporting' in postvars[0]):
                configData['SAVE_RESULT_REPORTING'] = True
            else:
                configData['SAVE_RESULT_REPORTING'] = False


            company_id = session['company_id']
            #Subscriptions.savesetting(postvars,company_id)
            result['EVALUATION_SETTING_DATA']=postvars
            result['company_id']=session['company_id']
            result['channel_id'] = postvars[0]['channelid']
            result['SETTING_DATA'] = configData

            returnValue = Configsettings.insertOrUpdateConfigSetting(result)
            returnValue = RegisteredEvaluationService.insertOrUpdateCompanySubscribedCategory(result)
            return redirect (url_for('companyadminsite.get_configSettingData',channel=result['channel_id'],sessionid=session['sessionid']),code=302)

    return redirect ('/company/admin')


@mod.route ('/graphreport', methods=['GET','POST'])
def get_companygraphreport():
    result=''
    if request.method == 'POST':
        graphreport = getgraphData(request.form)

    return json.dumps(graphreport)


def getgraphData(formData=None):
    graphreport={}
    # weeklyreport
    if('company_id' in session):
        companyid = session['company_id']
        todate=datetime.date.today ()
        weekbackdate=todate - datetime.timedelta (days=7)
        monthbackdate=todate - datetime.timedelta (days=30)

        channelid=None  # email
        userlist=None
        matrixlist=None
        statdate=todate
        enddate=todate

        if(formData is not None):
            userlist=request.form['userlist']  # "TEST_ADMIN,TEST_USER"#
        if userlist == '' or userlist is None:
            userlist=[]
        else:
            userlist=userlist.split (',')
        if (formData is not None):
            channelid=request.form['servicelist']  # "1,2"#
        if channelid == '' or channelid is None:
            channelid=[]
        else:
            channelid=channelid.split (',')
        if (formData is not None):
            matrixlist = request.form['subscriptionlist']  # "query_resolved,additional_education"#
        if matrixlist == '' or matrixlist is None:
            matrixlist = []
        else:
            matrixlist = matrixlist.split(',')

        result=QueryResults.getAverageMatrixResultByCompanyAndChannel (companyid, channelid, statdate, enddate, userlist,matrixlist)

        average_score=result['average_score']
        avg_today_score = int (average_score)
        if(avg_today_score > 100):
            avg_today_score = 100
        elif(avg_today_score <0):
            avg_today_score = 0

        graphreport['today']= avg_today_score

        statdate=weekbackdate
        result = QueryResults.getAverageMatrixResultByCompanyAndChannel(companyid, channelid, statdate, enddate, userlist,matrixlist)

        average_score = result['average_score']

        weekly_score = int (average_score)
        if (weekly_score > 100):
             weekly_score=100
        elif (weekly_score < 0):
             weekly_score=0
        graphreport['weekly']=int (weekly_score)

        statdate=monthbackdate
        result = QueryResults.getAverageMatrixResultByCompanyAndChannel(companyid, channelid, statdate, enddate, userlist,matrixlist)

        average_score = result['average_score']
        monthly_score = int (average_score)
        if (monthly_score > 100):
            monthly_score=100
        elif (monthly_score < 0):
            monthly_score=0

        graphreport['monthly']=monthly_score

        linegraphdata = QueryResults.getAverageScoreforLinegraph(companyid,userlist)
        graphreport['bargraph']=[{"userid": "1",
                              "data": linegraphdata
                              }]
    return graphreport

def splitTableFormData(formData):
    formJsonArrData = []
    fieldRepeatCount = 0
    for eachField in formData:
        values = formData.getlist(eachField)
        for index in range(len(values)):
            if len (formJsonArrData) > index:
                eachRowJson = formJsonArrData[index]
                if eachField not in eachRowJson:
                    eachRowJson[eachField] = values[index]
                else:
                    newRowJson = {}
                    newRowJson[eachField] = values[index]
                    formJsonArrData.append (newRowJson)
            else:
                newRowJson = {}
                newRowJson[eachField] = values[index]
                formJsonArrData.append (newRowJson)

    return formJsonArrData

def deleteUserSession(requestData):
    UserSession.deleteUserSession (requestData['sessionid'])

def retriveUserSessionData(requestData,request):
    if 'sessionid' in requestData:
        usersessiondata=UserSession.getSessionData (requestData['sessionid'],request)
        if (usersessiondata is not None):
            userData=json.loads (usersessiondata)
            session['user']=userData['user']
            session['name']=userData['name']
            session['user_id']=userData['user_id']
            session['company_id']=userData['company_id']
            session['enrole_to_service']=userData['enrole_to_service']
            session['role']=userData["role"]
            session['sessionid']=requestData['sessionid']
            return True
        session.pop ('user', None)
        session.pop ('company_id', None)
    return False



@mod.route('/abc',methods=['GET','POST'])
def abc():
    legend = "Date"
    conn =psycopg2.connect("dbname='csataidb' user='postgres' host='localhost' password='navedas'")
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT date from daily_stats")
        # data = cursor.fetchone()
        rows = cursor.fetchall()
        labels = list()
        i = 0
        for row in rows:
            labels.append(row[i])

        cursor.execute("SELECT no_of_interactions from daily_stats where user_id='102'")
        rows = cursor.fetchall()
        # Convert query to objects of key-value pairs
        values1 = list()
        i = 0
        for row in rows:
            values1.append(row[i])

        cursor.execute("SELECT no_of_interactions from daily_stats where user_id='101'")
        rows = cursor.fetchall()
        # Convert query to objects of key-value pairs
        values2 = list()
        i = 0
        for row in rows:
            values2.append(row[i])

        cursor.execute("SELECT user_name from daily_stats where id=8")
        rows = cursor.fetchall()
        # Convert query to objects of key-value pairs
        user1 = list()
        i = 0
        for row in rows:
            user1.append(row[i])
        cursor.execute("SELECT user_name from daily_stats where id=1")
        rows = cursor.fetchall()
        # Convert query to objects of key-value pairs
        user2 = list()
        i = 0
        for row in rows:
            user2.append(row[i])
        cursor.close()
        conn.close()
    except:
        print
        "Error: unable to fetch items"

    return render_template('chart.html', values1=values1,values2=values2, labels=labels, legend=legend,user1=user1,user2=user2)



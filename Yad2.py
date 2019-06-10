#!/usr/bin/env python
# -*- coding: utf-8 -*-


import pymongo
import itertools
import datetime
import smtplib
import re
import os
from selenium import webdriver
import time

class Yad2Monitor():
    def __init__(self):
        self.cars = {}
        
        user=os.environ.ge("mongo_user")
        password = os.environ.ge("mongo_user")
        
        assert user and password, "Missing credentilas for mongoDB"
        
        host = os.environ.ge("host")
        port = os.environ.ge("port")
        
        assert host and port, "Missing http connention details"
        
        uri = 'mongodb://{user}:{password}@{host}:{port}/yad2-project'.format(host=host, port=port, user=user, password=password)

        self.client = pymongo.MongoClient(uri)
        self.dbConnection = self.client.get_default_database()

    def getAllCarsModels(self):
        models = self.dbConnection['models']
        allModels = models.find({})
        return [(model.get("model"), model.get("url")) for model in allModels]

    def getAllCarsModelNames(self):
        models = self.dbConnection['models']
        allModels = models.find({})
        return [model.get("model") for model in allModels]

    def updateDB(self, model, newSuggestions):
        suggestions = self.dbConnection['suggestions']
        print "Updating DB with new results"
        suggestions.insert({"model": model, "suggestions": newSuggestions,
                            "date": datetime.datetime.strftime(datetime.datetime.now(), "%d-%b-%Y-%H:%M:%S")})

    def getOldFromDB(self, model):
        suggestions = self.dbConnection['suggestions']
        oldSuggestions = suggestions.find({"model": model})
        oldSuggestions = set(itertools.chain(*[Suggestion["suggestions"] for Suggestion in oldSuggestions]))
        return oldSuggestions

    def geResults(self, url):
        driver = webdriver.Chrome("C:\Python27\selenium\webdriver\chrome\chromedriver.exe")
        driver.get(url)
        time.sleep(15)

        if response.status_code == 200:
            # with open("car-{u}.html".format(u=uuid.uuid4()), "w") as f:
            #     print "Saving file..."
            #     f.write(str(driver.page_source))
            return driver.page_source
        else:
            raise Exception("Fail to fetch data")

    def cmpResults(self, model, newSuggestions):

        oldSuggestions = self.getOldFromDB(model)
        # print "old Suggestions: {o}".format(o=oldSuggestions)
        diff = {id: link for id, link in newSuggestions.items() if id not in oldSuggestions}
        return diff if diff else False

    def sendNotic(self, SUBJECT, TEXT, gmail,user, gmail_pwd, ,FROM, TO):
        # Prepare actual message
        message = """From: %s\nTo: %s\nSubject: %s\n\n%s
        """ % (FROM, TO, SUBJECT, TEXT)
        try:
            mailConnaction = smtplib.SMTP("smtp.gmail.com", 587)
            mailConnaction.ehlo()
            mailConnaction.starttls()
            mailConnaction.login(gmail_user, gmail_pwd)
            mailConnaction.sendmail(FROM, TO, message)
            mailConnaction.close()
            print 'successfully sent the mail subject: {subject}'.format(subject=SUBJECT)
        except:
            print "failed to send mail"

    def Run(self):
        timeSince = 0
        timeDelta = 30
        print "Welcome to Yad2feeder"
        print "**********************"
        print "Start Time: {time}".format(time=datetime.datetime.strftime(datetime.datetime.now(),"%d-%b-%Y-%H:%M:%S"))
        print "Searching Models on DB..."
        print "Found Models: \n\n{m}\n*********************************\n".format(m="\n".join(self.getAllCarsModelNames()))
        while True:
            for model, url in mon.getAllCarsModels():
                try:
                    print "Examining {v}".format(v=model)
                    htmlContant = mon.geResults(url)
                    Allsuggestions = {suggestion.split("=")[-1]: suggestion for suggestion in
                                      re.findall(r""""(Car_info.php\?CarID=.*)" """, htmlContant)}
                    print "Curr suggestions: {s}".format(s=Allsuggestions)
                    comparisonResult = mon.cmpResults(model=model, newSuggestions=Allsuggestions)
                    if comparisonResult:
                        print "New offers was found"
                        mon.updateDB(model, comparisonResult.keys())
                        links = "\n".join(["{indx}) http://www.yad2.co.il/Cars/{option}".format(
                            indx=indx + 1, option=option) for indx, option in enumerate(comparisonResult.values())])

                        mailBody = "Look at the following offer{s}\n\n{links}".format(
                            s=":" if len(comparisonResult) == 1 else "s:", links=links)

                        mon.sendNotic("New offer found for {model}".format(model=model), mailBody)
                    else:
                        print "Noting new for Now..."
                    print "<------------------------------------->\n"
                except Exception as e:
                    print "Exception... "
                    raise e

            nextSample = datetime.datetime.strftime(datetime.datetime.now() + datetime.timedelta(minutes=timeDelta),
                                                    "%d-%b-%Y-%H:%M:%S")

            timeSince += timeDelta
            if not timeSince % 600:
                mon.sendNotic("Yad2 feeder - keep alive", "I am waiting for new offers,")

            print "Next sample at: {d}".format(d=nextSample)
            time.sleep(timeDelta * 60)

if __name__ == "__main__":
    mon = Yad2Monitor()
    mon.Run()

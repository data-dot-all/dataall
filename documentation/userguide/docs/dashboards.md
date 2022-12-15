# **Dashboards**

Data.all connects with Amazon Quicksight to allow users to quickly visualize and analyse their data.

## **Start Quicksight session**

Go to the Dashboards menu of data.all and click on the orange "Quicksight" button in the top right corner. It will 
redirect you to the following page, in which you can start a Quicksight session in one of your environment accounts.
If *Dashboards* are not enabled in the environment, an error message will appear on the screen.

![qs](pictures/dashboards/qs_1.png#zoom#shadow)

## **Import a dashboard**
Our user has been working on a Dashboard in Quicksight and wants to register it and make it available in data.all. 
The first step is to copy the Dashboard ID to your clipboard. You can find this ID in the Quicksight URL.

![qs](pictures/dashboards/qs_2.png#zoom#shadow)

Now, go back to data.all and in the Dashboards menu, click on the *Import* button in the top-right corner. Fill in 
the following form and paste the dashboard ID correspondingly.

![qs](pictures/dashboards/qs_3.png#zoom#shadow)

## **Share a dashboard**
Once a dashboard is imported, it is catalogued in the central Catalog. Users can go to the Catalog, filter by dashboard
and request access to a dashboard as shown in the picture below.

![qs](pictures/dashboards/qs_4.png#zoom#shadow)

Once the request is open, the Dashboard owner team can accept or reject the request in the Dashboard *Shares* tab. If 
the request is approved, the requesters' team can visualize the Dashboard directly from data.all UI.

!!! warning "Session capacity pricing"
    To be able to embed the Dashboard using anonymous sessions, Session Capacity pricing needs to be enabled in the source
    Quicksight account. A Quicksight administrator in the AWS account needs to go to the **Manage Quicksight** menu and
    enable capacity pricing.

![qs](pictures/dashboards/qs_5.png#zoom#shadow)




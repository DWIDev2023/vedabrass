def onlinestore_schema():
    return [{
        "@type":"OnlineStore",
        "@id":"https://vedabrass.com/#store",
        "name":"VedaBrass",
        "url":"https://vedabrass.com",
        "parentOrganization":{
            "@id":"https://vedabrass.com/#organization"
        },
        "image":"https://vedabrass.com/static/front/images/logo.png",
        "currenciesAccepted":"INR",
        "paymentAccepted":[
            "Credit Card",
            "Debit Card",
            "UPI",
            "Net Banking",
            "Cash on Delivery"
        ]
    }]
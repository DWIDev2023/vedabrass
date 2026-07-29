def organization_schema():
    return [{
        "@type": "Organization",
        "@id":"https://vedabrass.com/#organization",
        "name": "VedaBrass",
        "brand": {
            "@type": "Brand",
            "name": "VedaBrass"
        },
        "url": "https://vedabrass.com",
        "logo": {
            "@type": "ImageObject",
            "url": "https://vedabrass.com/static/front/images/logo.png"
        },
        "image":{
            "@type":"ImageObject",
            "url":"https://vedabrass.com/static/front/images/logo.png"
        },
        "sameAs": [
            "https://www.facebook.com/vedabrassofficial",
            "https://www.instagram.com/vedabrassofficial/",
            "https://www.youtube.com/@VedabrassOfficial"
        ],
        "contactPoint":[{
            "@type":"ContactPoint",
            "contactType":"customer support",
            "telephone":"+91-87124-95444",
            "areaServed":"IN",
            "availableLanguage":[
                "English",
                "Hindi",
                "Telugu"
            ]
        }],
        "areaServed":{
            "@type":"Country",
            "name":"India"
        },
        "foundingLocation":{
            "@type":"Place",
            "address":{
                "@type":"PostalAddress",
                "addressLocality":"Hyderabad",
                "addressRegion":"Telangana",
                "addressCountry":"IN"
            }
        },
        "address": {
            "@type": "PostalAddress",
            "streetAddress": "L3-16, IDA Kukatpally",
            "addressLocality": "Hyderabad",
            "addressRegion": "Telangana",
            "postalCode": "500072",
            "addressCountry": "IN"
        },
        "email":"hello@vedabrass.com",
        "knowsAbout":[
            "Brass Idols",
            "Brass Decor",
            "Pooja Articles",
            "Traditional Brass Crafts",
            "Brass Kitchenware"
        ]
    }]
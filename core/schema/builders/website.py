def website_schema():
    return [{
        "@type": "WebSite",
        "@id":"https://vedabrass.com/#website",
        "url": "https://vedabrass.com",
        "publisher":{
            "@id":"https://vedabrass.com/#organization"
        },
        "name": "VedaBrass",
        "potentialAction": {
            "@type": "SearchAction",
            "target": {
                "@type": "EntryPoint",
                "urlTemplate": "https://vedabrass.com/search-products?q={search_term_string}"
            },
            "query-input": "required name=search_term_string"
        }
    }]
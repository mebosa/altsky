with open('frontend/static/sitemap.xml', 'rb') as f:
    content = f.read()
    print(content[:100])

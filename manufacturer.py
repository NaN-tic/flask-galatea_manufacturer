from flask import Blueprint, render_template, current_app, abort, url_for, g, \
    request, session, redirect
from flask.ext.paginate import Pagination
from flask.ext.babel import gettext as _, lazy_gettext
from galatea.tryton import tryton

manufacturer = Blueprint('manufacturer', __name__, template_folder='templates')

DISPLAY_MSG = lazy_gettext('Displaying <b>{start} - {end}</b> of <b>{total}</b>')

GALATEA_WEBSITE = current_app.config.get('TRYTON_GALATEA_SITE')
SHOP = current_app.config.get('TRYTON_SALE_SHOP')
LIMIT = current_app.config.get('TRYTON_PAGINATION_CATALOG_LIMIT', 20)

Website = tryton.pool.get('galatea.website')
WebSiteManufacturer = tryton.pool.get('galatea.website')
Template = tryton.pool.get('product.template')
Product = tryton.pool.get('product.product')

MANUFACTURER_TEMPLATE_FIELD_NAMES = [
    'name', 'code', 'esale_slug', 'esale_shortdescription', 'esale_price',
    'esale_default_images', 'esale_all_images', 'esale_new', 'esale_hot',
    'esale_sequence', 'template_attributes', 'products',
    ]
MANUFACTURER_PRODUCT_FIELD_NAMES = [
    'code', 'template', 'attributes', 'add_cart', 'quantity', 'forecast_quantity',
    ]
MANUFACTURER_TEMPLATE_FILTERS = []

@manufacturer.route("/manufacturer/<slug>", methods=["GET", "POST"], endpoint="manufacturer_product_en")
@manufacturer.route("/fabricante/<slug>", methods=["GET", "POST"], endpoint="manufacturer_product_es")
@manufacturer.route("/fabricant/<slug>", methods=["GET", "POST"], endpoint="manufacturer_product_ca")
@tryton.transaction()
def manufacturer_products(lang, slug):
    '''Products by manufacturer'''

    websites = Website.search([
        ('id', '=', GALATEA_WEBSITE),
        ], limit=1)
    if not websites:
        abort(404)
    website, = websites

    manufacturers = website.manufacturers

    manufacturer = None
    for m in website.manufacturers:
        if m.slug == slug:
            manufacturer = m
            break
    if not manufacturer:
        # change 404 to all manufacturer list
        return redirect(url_for('.manufacturer_'+g.language, lang=g.language))

    # limit
    if request.args.get('limit'):
        try:
            limit = int(request.args.get('limit'))
            session['catalog_limit'] = limit
        except:
            limit = LIMIT
    else:
        limit = session.get('catalog_limit', LIMIT)

    # view
    if request.args.get('view'):
        view = 'grid'
        if request.args.get('view') == 'list':
            view = 'list'
        session['catalog_view'] = view

    order = []

    try:
        page = int(request.args.get('page', 1))
    except ValueError:
        page = 1

    domain_filter = session.get('manufacturer_filter', [])
    if request.form:
        domain_filter = []
        domain_filter_keys = set()
        for k, v in request.form.iteritems():
            if k in MANUFACTURER_TEMPLATE_FILTERS:
                domain_filter_keys.add(k)

        for k in list(domain_filter_keys):
            domain_filter.append((k, 'in', request.form.getlist(k)))

    session['manufacturer_filter'] = domain_filter

    domain = [
        ('esale_available', '=', True),
        ('esale_active', '=', True),
        ('esale_saleshops', 'in', [SHOP]),
        ('manufacturer', '=', manufacturer.party.id),
        ] + domain_filter
    total = Template.search_count(domain)
    offset = (page-1)*limit

    tpls = Template.search_read(domain, offset, limit, order, MANUFACTURER_TEMPLATE_FIELD_NAMES)

    product_domain = [('template', 'in', [tpl['id'] for tpl in tpls])]
    prds = Product.search_read(product_domain, fields_names=MANUFACTURER_PRODUCT_FIELD_NAMES)

    products = []
    for tpl in tpls:
        prods = []
        for prd in prds:
            if prd['template'] == tpl['id']:
                prods.append(prd)
        tpl['products'] = prods
        products.append(tpl)

    pagination = Pagination(page=page, total=total, per_page=limit, display_msg=DISPLAY_MSG, bs_version='3')

    #breadcumbs
    breadcrumbs = [{
        'slug': url_for('catalog.catalog', lang=g.language),
        'name': _('Catalog'),
        }, {
        'slug': url_for('.manufacturer_'+g.language, lang=g.language),
        'name': _('Manufacturers'),
        }, {
        'slug': url_for('.manufacturer_product_'+g.language, lang=g.language, slug=slug),
        'name': manufacturer.party.name,
        }]

    return render_template('catalog-manufacturer.html',
            website=website,
            manufacturer=manufacturer,
            manufacturers=manufacturers,
            breadcrumbs=breadcrumbs,
            pagination=pagination,
            products=products,
            )

@manufacturer.route("/manufacturer/", endpoint="manufacturer_en")
@manufacturer.route("/fabricante/", endpoint="manufacturer_es")
@manufacturer.route("/fabricant/", endpoint="manufacturer_ca")
@tryton.transaction()
def manufacturer_all(lang):
    '''All manufacturers'''

    websites = Website.search([
        ('id', '=', GALATEA_WEBSITE),
        ], limit=1)
    if not websites:
        abort(404)
    website, = websites

    manufacturers = website.manufacturers

    #breadcumbs
    breadcrumbs = [{
        'slug': url_for('catalog.catalog', lang=g.language),
        'name': _('Catalog'),
        }, {
        'slug': url_for('.manufacturer_'+g.language, lang=g.language),
        'name': _('Manufacturers'),
        }]

    return render_template('catalog-manufacturers.html',
            website=website,
            manufacturers=manufacturers,
            breadcrumbs=breadcrumbs,
            )

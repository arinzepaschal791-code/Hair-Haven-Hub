# ========== CONTINUATION FROM WHERE YOUR CODE WAS CUT OFF ==========

@app.route('/account/edit', methods=['GET', 'POST'])
@customer_required
def edit_account():
    """Edit customer account"""
    customer = Customer.query.get(session['customer_id'])
    
    if request.method == 'POST':
        try:
            customer.first_name = request.form.get('first_name', customer.first_name)
            customer.last_name = request.form.get('last_name', customer.last_name)
            customer.phone = request.form.get('phone', customer.phone)
            customer.address = request.form.get('address', customer.address)
            customer.city = request.form.get('city', customer.city)
            customer.state = request.form.get('state', customer.state)
            
            # Check if password change is requested
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            
            if current_password and new_password:
                if customer.check_password(current_password):
                    customer.set_password(new_password)
                    flash('Password changed successfully!', 'success')
                else:
                    flash('Current password is incorrect', 'danger')
                    return redirect(url_for('edit_account'))
            
            db.session.commit()
            session['customer_name'] = customer.full_name
            flash('Account updated successfully!', 'success')
            return redirect(url_for('account'))
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Edit account error: {str(e)}", file=sys.stderr)
            flash('Error updating account. Please try again.', 'danger')
    
    return render_template('edit_account.html', customer=customer, config=BUSINESS_CONFIG)

# ========== CHECKOUT ROUTES ==========

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    """Checkout page"""
    if 'customer_id' not in session:
        session['pending_checkout'] = True
        flash('Please login to complete your order', 'warning')
        return redirect(url_for('customer_login'))
    
    cart_items = session.get('cart', [])
    if not cart_items:
        flash('Your cart is empty!', 'warning')
        return redirect(url_for('shop'))
    
    # Calculate totals
    subtotal = calculate_cart_total()
    delivery_fee = 3000  # Default Lagos delivery
    if subtotal >= 150000:
        delivery_fee = 0
    total = subtotal + delivery_fee
    
    if request.method == 'POST':
        try:
            # Get form data
            name = request.form.get('name')
            email = request.form.get('email')
            phone = request.form.get('phone')
            address = request.form.get('address')
            city = request.form.get('city')
            state = request.form.get('state')
            payment_method = request.form.get('payment_method', 'bank_transfer')
            notes = request.form.get('notes', '')
            
            # Validate required fields
            if not all([name, email, phone, address, city, state]):
                flash('Please fill in all required fields.', 'danger')
                return redirect(url_for('checkout'))
            
            # Adjust delivery fee based on city
            if city.lower() in ['lagos', 'ikeja', 'vi', 'lekki', 'ikoyi', 'surulere', 'yaba', 'ajah']:
                delivery_fee = 3000 if subtotal < 150000 else 0
            else:
                delivery_fee = 5000 if subtotal < 150000 else 0
            
            total = subtotal + delivery_fee
            
            # Create order
            order = Order(
                order_number=generate_order_number(),
                customer_id=session['customer_id'],
                customer_name=name,
                customer_email=email,
                customer_phone=phone,
                shipping_address=address,
                shipping_city=city,
                shipping_state=state,
                total_amount=subtotal,
                shipping_amount=delivery_fee,
                final_amount=total,
                payment_method=payment_method,
                notes=notes
            )
            
            db.session.add(order)
            db.session.flush()
            
            # Add order items
            for item in cart_items:
                product = Product.query.get(item['id'])
                if product:
                    # Update product quantity
                    if product.quantity < item['quantity']:
                        flash(f'Insufficient stock for {product.name}. Only {product.quantity} left.', 'danger')
                        return redirect(url_for('cart'))
                    
                    product.quantity -= item['quantity']
                    
                    order_item = OrderItem(
                        order_id=order.id,
                        product_id=product.id,
                        product_name=product.name,
                        quantity=item['quantity'],
                        unit_price=item['price'],
                        total_price=item['price'] * item['quantity']
                    )
                    db.session.add(order_item)
            
            db.session.commit()
            
            # Clear cart
            session.pop('cart', None)
            
            flash(f'Order #{order.order_number} created successfully! We will contact you shortly.', 'success')
            return render_template('order.html',
                                 order=order,
                                 bank_details=BUSINESS_CONFIG,
                                 config=BUSINESS_CONFIG)
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Checkout error: {str(e)}", file=sys.stderr)
            flash('Error processing order. Please try again.', 'danger')
            return redirect(url_for('checkout'))
    
    # GET request - show checkout form
    customer = None
    if 'customer_id' in session:
        customer = Customer.query.get(session['customer_id'])
    
    return render_template('checkout.html',
                         cart_items=cart_items,
                         subtotal=subtotal,
                         delivery_fee=delivery_fee,
                         total=total,
                         free_delivery_threshold=150000,
                         customer=customer,
                         config=BUSINESS_CONFIG)

@app.route('/order/<int:id>')
@customer_required
def view_order(id):
    """View order details"""
    try:
        order = Order.query.get_or_404(id)
        
        # Check if order belongs to current customer
        if order.customer_id != session['customer_id'] and not session.get('is_admin'):
            flash('You do not have permission to view this order.', 'danger')
            return redirect(url_for('account'))
        
        order_items = OrderItem.query.filter_by(order_id=order.id).all()
        
        return render_template('order_detail.html',
                             order=order,
                             order_items=order_items,
                             config=BUSINESS_CONFIG)
    except Exception as e:
        print(f"❌ View order error: {str(e)}", file=sys.stderr)
        flash('Error loading order details.', 'danger')
        return redirect(url_for('account'))

# ========== ABOUT & CONTACT ROUTES ==========

@app.route('/about')
def about():
    """About page"""
    return render_template('about.html', config=BUSINESS_CONFIG)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact page"""
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            email = request.form.get('email')
            subject = request.form.get('subject')
            message = request.form.get('message')
            
            if not all([name, email, subject, message]):
                flash('All fields are required.', 'danger')
                return redirect(url_for('contact'))
            
            # Save contact message to database
            contact_msg = ContactMessage(
                name=name,
                email=email,
                subject=subject,
                message=message
            )
            
            db.session.add(contact_msg)
            db.session.commit()
            
            flash('Your message has been sent successfully! We will contact you soon.', 'success')
            return redirect(url_for('contact'))
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Contact form error: {str(e)}", file=sys.stderr)
            flash('Error sending message. Please try again.', 'danger')
    
    return render_template('contact.html', config=BUSINESS_CONFIG)

# ========== REVIEW ROUTES ==========

@app.route('/add-review/<int:product_id>', methods=['POST'])
@customer_required
def add_review(product_id):
    """Add product review"""
    try:
        product = Product.query.get_or_404(product_id)
        rating = int(request.form.get('rating', 5))
        comment = request.form.get('comment', '')
        
        if not comment:
            flash('Please provide a review comment.', 'warning')
            return redirect(url_for('product_detail', id=product_id))
        
        customer = Customer.query.get(session['customer_id'])
        
        # Check if customer already reviewed this product
        existing_review = Review.query.filter_by(
            product_id=product_id,
            email=customer.email
        ).first()
        
        if existing_review:
            flash('You have already reviewed this product.', 'warning')
            return redirect(url_for('product_detail', id=product_id))
        
        review = Review(
            product_id=product_id,
            customer_name=customer.full_name,
            email=customer.email,
            rating=rating,
            comment=comment,
            location=customer.city or 'Unknown',
            approved=False  # Admin needs to approve reviews
        )
        
        db.session.add(review)
        db.session.commit()
        
        flash('Thank you for your review! It will be visible after approval.', 'success')
        return redirect(url_for('product_detail', id=product_id))
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Add review error: {str(e)}", file=sys.stderr)
        flash('Error submitting review. Please try again.', 'danger')
        return redirect(url_for('product_detail', id=product_id))

# ========== NEWSLETTER ROUTES ==========

@app.route('/subscribe-newsletter', methods=['POST'])
def subscribe_newsletter():
    """Subscribe to newsletter"""
    try:
        email = request.form.get('email')
        
        if not email:
            flash('Please enter your email address.', 'warning')
            return redirect(request.referrer or url_for('index'))
        
        # Check if already subscribed
        existing = NewsletterSubscriber.query.filter_by(email=email).first()
        if existing:
            if existing.subscribed:
                flash('You are already subscribed to our newsletter.', 'info')
            else:
                existing.subscribed = True
                db.session.commit()
                flash('Successfully resubscribed to our newsletter!', 'success')
        else:
            subscriber = NewsletterSubscriber(email=email)
            db.session.add(subscriber)
            db.session.commit()
            flash('Successfully subscribed to our newsletter!', 'success')
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Newsletter subscription error: {str(e)}", file=sys.stderr)
        flash('Error subscribing to newsletter. Please try again.', 'danger')
    
    return redirect(request.referrer or url_for('index'))

# ========== ADMIN ROUTES ==========

@app.route('/admin', methods=['GET', 'POST'])
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login"""
    # If already logged in, redirect to dashboard
    if 'admin_id' in session and session.get('is_admin'):
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        try:
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()
            
            # Query admin user
            admin = User.query.filter_by(username=username, is_admin=True).first()
            
            if admin and admin.check_password(password):
                session['admin_id'] = admin.id
                session['admin_name'] = admin.username
                session['is_admin'] = True
                session.permanent = True
                
                flash('Admin login successful!', 'success')
                return redirect(url_for('admin_dashboard'))
            else:
                flash('Invalid admin credentials. Use admin/admin123', 'danger')
                
        except Exception as e:
            print(f"❌ Admin login error: {str(e)}", file=sys.stderr)
            flash('Login error. Please try again.', 'danger')
    
    return render_template('admin/admin_login.html', config=BUSINESS_CONFIG)

@app.route('/admin/logout')
def admin_logout():
    """Admin logout"""
    session.pop('admin_id', None)
    session.pop('admin_name', None)
    session.pop('is_admin', None)
    flash('Admin logged out successfully.', 'info')
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """Admin dashboard"""
    try:
        stats = get_dashboard_stats()
        
        # Get recent orders
        recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
        
        # Get low stock products
        low_stock_products = Product.query.filter(
            Product.quantity > 0,
            Product.quantity <= 5
        ).order_by(Product.quantity).limit(5).all()
        
        # Get top products
        top_products = Product.query.order_by(Product.quantity.desc()).limit(5).all()
        
        # Get recent customers
        recent_customers = Customer.query.order_by(Customer.created_at.desc()).limit(5).all()
        
        # Get recent reviews
        recent_reviews = Review.query.filter_by(approved=False).order_by(Review.created_at.desc()).limit(5).all()
        
        # Get today's date for display
        now = datetime.now()
        
        return render_template('admin/admin_dashboard.html',
                             stats=stats,
                             recent_orders=recent_orders,
                             low_stock_products=low_stock_products,
                             top_products=top_products,
                             recent_customers=recent_customers,
                             recent_reviews=recent_reviews,
                             now=now,
                             config=BUSINESS_CONFIG)
    except Exception as e:
        print(f"❌ Admin dashboard error: {str(e)}", file=sys.stderr)
        flash('Error loading dashboard.', 'danger')
        return render_template('admin/admin_dashboard.html',
                             stats=get_dashboard_stats(),
                             recent_orders=[],
                             low_stock_products=[],
                             top_products=[],
                             recent_customers=[],
                             recent_reviews=[],
                             now=datetime.now(),
                             config=BUSINESS_CONFIG)

# ========== ADMIN API ENDPOINTS ==========

@app.route('/admin/api/dashboard-data')
@admin_required
def admin_api_dashboard_data():
    """API endpoint for dashboard data"""
    try:
        stats = get_dashboard_stats()
        
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        print(f"❌ Dashboard API error: {str(e)}", file=sys.stderr)
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/api/update-order-status/<int:id>', methods=['POST'])
@admin_required
def admin_api_update_order_status(id):
    """API endpoint to update order status"""
    try:
        order = Order.query.get_or_404(id)
        data = request.get_json()
        
        if 'status' in data:
            order.status = data['status']
            order.updated_at = datetime.utcnow()
            
            # Update payment status if order is delivered
            if data['status'] == 'delivered' and order.payment_status == 'pending':
                order.payment_status = 'paid'
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Order status updated to {order.status}',
                'order': {
                    'id': order.id,
                    'order_number': order.order_number,
                    'status': order.status,
                    'payment_status': order.payment_status
                }
            })
        
        return jsonify({'success': False, 'error': 'Status not provided'}), 400
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Update order status API error: {str(e)}", file=sys.stderr)
        return jsonify({'success': False, 'error': str(e)}), 500

# ========== ADMIN PRODUCTS ROUTES ==========

@app.route('/admin/products')
@admin_required
def admin_products():
    """Admin products list"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 20
        search = request.args.get('search', '')
        category_id = request.args.get('category_id', type=int)
        
        query = Product.query
        
        if search:
            query = query.filter(Product.name.ilike(f'%{search}%'))
        
        if category_id:
            query = query.filter_by(category_id=category_id)
        
        products = query.order_by(Product.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        categories = Category.query.all()
        
        return render_template('admin/products.html',
                             products=products,
                             categories=categories,
                             search=search,
                             category_id=category_id,
                             config=BUSINESS_CONFIG)
    except Exception as e:
        print(f"❌ Admin products error: {str(e)}", file=sys.stderr)
        flash('Error loading products.', 'danger')
        return render_template('admin/products.html',
                             products=[],
                             categories=[],
                             config=BUSINESS_CONFIG)

@app.route('/admin/products/add', methods=['GET', 'POST'])
@admin_required
def admin_add_product():
    """Add product"""
    if request.method == 'POST':
        try:
            # Handle form data
            name = request.form.get('name')
            description = request.form.get('description')
            price = float(request.form.get('price', 0))
            compare_price = request.form.get('compare_price')
            cost_price = request.form.get('cost_price')
            quantity = int(request.form.get('quantity', 0))
            category_id = int(request.form.get('category_id'))
            sku = request.form.get('sku')
            length = request.form.get('length')
            weight = request.form.get('weight')
            texture = request.form.get('texture')
            color = request.form.get('color')
            colors = request.form.get('colors')
            specifications = request.form.get('specifications')
            care_instructions = request.form.get('care_instructions')
            featured = 'featured' in request.form
            active = 'active' in request.form
            
            # Generate slug and SKU if not provided
            slug = name.lower().replace(' ', '-').replace('"', '').replace("'", '')
            if not sku:
                sku = f"NHL-{random.randint(1000, 9999)}"
            
            # Create product
            product = Product(
                name=name,
                slug=slug,
                description=description,
                price=price,
                compare_price=float(compare_price) if compare_price else None,
                cost_price=float(cost_price) if cost_price else None,
                quantity=quantity,
                sku=sku,
                category_id=category_id,
                featured=featured,
                active=active,
                length=length,
                weight=weight,
                texture=texture,
                color=color,
                colors=colors,
                specifications=specifications,
                care_instructions=care_instructions
            )
            
            # Handle image upload
            if 'image' in request.files:
                image_file = request.files['image']
                if image_file and allowed_file(image_file.filename):
                    filename = secure_filename(f"{uuid.uuid4()}.{image_file.filename.split('.')[-1]}")
                    image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    image_file.save(image_path)
                    product.image_url = f"uploads/{filename}"
            
            # Handle video upload
            if 'video' in request.files:
                video_file = request.files['video']
                if video_file and allowed_file(video_file.filename):
                    filename = secure_filename(f"{uuid.uuid4()}.{video_file.filename.split('.')[-1]}")
                    video_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    video_file.save(video_path)
                    product.video_url = f"uploads/{filename}"
            
            db.session.add(product)
            db.session.commit()
            
            flash(f'Product "{name}" added successfully!', 'success')
            return redirect(url_for('admin_products'))
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Add product error: {str(e)}", file=sys.stderr)
            flash('Error adding product. Please try again.', 'danger')
    
    categories = Category.query.all()
    return render_template('admin/add_product.html', categories=categories, config=BUSINESS_CONFIG)

@app.route('/admin/products/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_product(id):
    """Edit product"""
    product = Product.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Update product data
            product.name = request.form.get('name')
            product.description = request.form.get('description')
            product.price = float(request.form.get('price', 0))
            
            compare_price = request.form.get('compare_price')
            product.compare_price = float(compare_price) if compare_price else None
            
            cost_price = request.form.get('cost_price')
            product.cost_price = float(cost_price) if cost_price else None
            
            product.quantity = int(request.form.get('quantity', 0))
            product.category_id = int(request.form.get('category_id'))
            product.sku = request.form.get('sku')
            product.length = request.form.get('length')
            product.weight = request.form.get('weight')
            product.texture = request.form.get('texture')
            product.color = request.form.get('color')
            product.colors = request.form.get('colors')
            product.specifications = request.form.get('specifications')
            product.care_instructions = request.form.get('care_instructions')
            product.featured = 'featured' in request.form
            product.active = 'active' in request.form
            
            # Update slug
            product.slug = product.name.lower().replace(' ', '-').replace('"', '').replace("'", '')
            
            # Handle image upload
            if 'image' in request.files:
                image_file = request.files['image']
                if image_file and allowed_file(image_file.filename):
                    filename = secure_filename(f"{uuid.uuid4()}.{image_file.filename.split('.')[-1]}")
                    image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    image_file.save(image_path)
                    product.image_url = f"uploads/{filename}"
            
            # Handle video upload
            if 'video' in request.files:
                video_file = request.files['video']
                if video_file and allowed_file(video_file.filename):
                    filename = secure_filename(f"{uuid.uuid4()}.{video_file.filename.split('.')[-1]}")
                    video_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    video_file.save(video_path)
                    product.video_url = f"uploads/{filename}"
            
            db.session.commit()
            
            flash(f'Product "{product.name}" updated successfully!', 'success')
            return redirect(url_for('admin_products'))
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Edit product error: {str(e)}", file=sys.stderr)
            flash('Error updating product. Please try again.', 'danger')
    
    categories = Category.query.all()
    return render_template('admin/edit_product.html', product=product, categories=categories, config=BUSINESS_CONFIG)

@app.route('/admin/products/delete/<int:id>', methods=['POST'])
@admin_required
def admin_delete_product(id):
    """Delete product"""
    try:
        product = Product.query.get_or_404(id)
        product_name = product.name
        
        # Check if product has orders
        order_items = OrderItem.query.filter_by(product_id=id).count()
        if order_items > 0:
            flash(f'Cannot delete "{product_name}" because it has {order_items} order(s) associated with it.', 'danger')
            return redirect(url_for('admin_products'))
        
        db.session.delete(product)
        db.session.commit()
        
        flash(f'Product "{product_name}" deleted successfully!', 'success')
        return redirect(url_for('admin_products'))
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Delete product error: {str(e)}", file=sys.stderr)
        flash('Error deleting product. Please try again.', 'danger')
        return redirect(url_for('admin_products'))

# ========== ADMIN ORDERS ROUTES ==========

@app.route('/admin/orders')
@admin_required
def admin_orders():
    """Admin orders"""
    try:
        status = request.args.get('status', 'all')
        payment_status = request.args.get('payment_status', 'all')
        search = request.args.get('search', '')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        page = request.args.get('page', 1, type=int)
        per_page = 20
        
        query = Order.query
        
        if status != 'all':
            query = query.filter_by(status=status)
        
        if payment_status != 'all':
            query = query.filter_by(payment_status=payment_status)
        
        if search:
            query = query.filter(
                (Order.order_number.ilike(f'%{search}%')) |
                (Order.customer_name.ilike(f'%{search}%')) |
                (Order.customer_email.ilike(f'%{search}%'))
            )
        
        if start_date:
            query = query.filter(Order.created_at >= start_date)
        
        if end_date:
            query = query.filter(Order.created_at <= end_date + ' 23:59:59')
        
        orders = query.order_by(Order.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Get order statistics
        order_stats = {
            'total': Order.query.count(),
            'pending': Order.query.filter_by(status='pending').count(),
            'processing': Order.query.filter_by(status='processing').count(),
            'shipped': Order.query.filter_by(status='shipped').count(),
            'delivered': Order.query.filter_by(status='delivered').count(),
            'cancelled': Order.query.filter_by(status='cancelled').count()
        }
        
        return render_template('admin/orders.html',
                             orders=orders,
                             order_stats=order_stats,
                             status=status,
                             payment_status=payment_status,
                             search=search,
                             start_date=start_date,
                             end_date=end_date,
                             config=BUSINESS_CONFIG)
    except Exception as e:
        print(f"❌ Admin orders error: {str(e)}", file=sys.stderr)
        flash('Error loading orders.', 'danger')
        return render_template('admin/orders.html',
                             orders=[],
                             order_stats={},
                             config=BUSINESS_CONFIG)

@app.route('/admin/orders/<int:id>')
@admin_required
def admin_order_detail(id):
    """Order detail"""
    try:
        order = Order.query.get_or_404(id)
        order_items = OrderItem.query.filter_by(order_id=order.id).all()
        
        return render_template('admin/order_detail.html',
                             order=order,
                             order_items=order_items,
                             config=BUSINESS_CONFIG)
    except Exception as e:
        print(f"❌ Admin order detail error: {str(e)}", file=sys.stderr)
        flash('Error loading order details.', 'danger')
        return redirect(url_for('admin_orders'))

@app.route('/admin/orders/update-status/<int:id>', methods=['POST'])
@admin_required
def admin_update_order_status(id):
    """Update order status"""
    try:
        order = Order.query.get_or_404(id)
        new_status = request.form.get('status')
        
        if new_status:
            order.status = new_status
            order.updated_at = datetime.utcnow()
            
            # If status is delivered, mark payment as paid
            if new_status == 'delivered' and order.payment_status == 'pending':
                order.payment_status = 'paid'
            
            db.session.commit()
            
            flash(f'Order #{order.order_number} status updated to {new_status}', 'success')
        
        return redirect(url_for('admin_order_detail', id=id))
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Update order status error: {str(e)}", file=sys.stderr)
        flash('Error updating order status.', 'danger')
        return redirect(url_for('admin_order_detail', id=id))

@app.route('/admin/orders/update-payment-status/<int:id>', methods=['POST'])
@admin_required
def admin_update_payment_status(id):
    """Update payment status"""
    try:
        order = Order.query.get_or_404(id)
        new_status = request.form.get('payment_status')
        
        if new_status:
            order.payment_status = new_status
            order.updated_at = datetime.utcnow()
            db.session.commit()
            
            flash(f'Order #{order.order_number} payment status updated to {new_status}', 'success')
        
        return redirect(url_for('admin_order_detail', id=id))
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Update payment status error: {str(e)}", file=sys.stderr)
        flash('Error updating payment status.', 'danger')
        return redirect(url_for('admin_order_detail', id=id))

@app.route('/admin/orders/add-tracking/<int:id>', methods=['POST'])
@admin_required
def admin_add_tracking(id):
    """Add tracking number"""
    try:
        order = Order.query.get_or_404(id)
        tracking_number = request.form.get('tracking_number')
        
        if tracking_number:
            order.tracking_number = tracking_number
            order.status = 'shipped'
            order.updated_at = datetime.utcnow()
            db.session.commit()
            
            flash(f'Tracking number added for Order #{order.order_number}', 'success')
        
        return redirect(url_for('admin_order_detail', id=id))
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Add tracking error: {str(e)}", file=sys.stderr)
        flash('Error adding tracking number.', 'danger')
        return redirect(url_for('admin_order_detail', id=id))

@app.route('/admin/orders/delete/<int:id>', methods=['POST'])
@admin_required
def admin_delete_order(id):
    """Delete order"""
    try:
        order = Order.query.get_or_404(id)
        order_number = order.order_number
        
        # Delete order items first (cascade should handle this)
        OrderItem.query.filter_by(order_id=id).delete()
        
        # Delete order
        db.session.delete(order)
        db.session.commit()
        
        flash(f'Order #{order_number} deleted successfully!', 'success')
        return redirect(url_for('admin_orders'))
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Delete order error: {str(e)}", file=sys.stderr)
        flash('Error deleting order.', 'danger')
        return redirect(url_for('admin_orders'))

# ========== ADMIN CUSTOMERS ROUTES ==========

@app.route('/admin/customers')
@admin_required
def admin_customers():
    """Admin customers list"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 20
        search = request.args.get('search', '')
        
        query = Customer.query
        
        if search:
            query = query.filter(
                (Customer.email.ilike(f'%{search}%')) |
                (Customer.first_name.ilike(f'%{search}%')) |
                (Customer.last_name.ilike(f'%{search}%')) |
                (Customer.phone.ilike(f'%{search}%'))
            )
        
        customers = query.order_by(Customer.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return render_template('admin/customers.html',
                             customers=customers,
                             search=search,
                             config=BUSINESS_CONFIG)
    except Exception as e:
        print(f"❌ Admin customers error: {str(e)}", file=sys.stderr)
        flash('Error loading customers.', 'danger')
        return render_template('admin/customers.html',
                             customers=[],
                             config=BUSINESS_CONFIG)

@app.route('/admin/customers/<int:id>')
@admin_required
def admin_customer_detail(id):
    """Customer detail"""
    try:
        customer = Customer.query.get_or_404(id)
        orders = Order.query.filter_by(customer_id=customer.id).order_by(Order.created_at.desc()).all()
        
        return render_template('admin/customer_detail.html',
                             customer=customer,
                             orders=orders,
                             config=BUSINESS_CONFIG)
    except Exception as e:
        print(f"❌ Admin customer detail error: {str(e)}", file=sys.stderr)
        flash('Error loading customer details.', 'danger')
        return redirect(url_for('admin_customers'))

# ========== ADMIN REVIEWS ROUTES ==========

@app.route('/admin/reviews')
@admin_required
def admin_reviews():
    """Admin reviews"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 20
        approved = request.args.get('approved', 'all')
        
        query = Review.query
        
        if approved == 'pending':
            query = query.filter_by(approved=False)
        elif approved == 'approved':
            query = query.filter_by(approved=True)
        
        reviews = query.order_by(Review.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return render_template('admin/reviews.html',
                             reviews=reviews,
                             approved=approved,
                             config=BUSINESS_CONFIG)
    except Exception as e:
        print(f"❌ Admin reviews error: {str(e)}", file=sys.stderr)
        flash('Error loading reviews.', 'danger')
        return render_template('admin/reviews.html',
                             reviews=[],
                             config=BUSINESS_CONFIG)

@app.route('/admin/reviews/approve/<int:id>', methods=['POST'])
@admin_required
def admin_approve_review(id):
    """Approve review"""
    try:
        review = Review.query.get_or_404(id)
        review.approved = True
        db.session.commit()
        
        flash('Review approved successfully!', 'success')
        return redirect(url_for('admin_reviews'))
        
    except Exception as e:
        db.session.rollback()
        flash('Error approving review.', 'danger')
        return redirect(url_for('admin_reviews'))

@app.route('/admin/reviews/delete/<int:id>', methods=['POST'])
@admin_required
def admin_delete_review(id):
    """Delete review"""
    try:
        review = Review.query.get_or_404(id)
        db.session.delete(review)
        db.session.commit()
        
        flash('Review deleted successfully!', 'success')
        return redirect(url_for('admin_reviews'))
        
    except Exception as e:
        db.session.rollback()
        flash('Error deleting review.', 'danger')
        return redirect(url_for('admin_reviews'))

# ========== ADMIN CATEGORIES ROUTES ==========

@app.route('/admin/categories')
@admin_required
def admin_categories():
    """Admin categories"""
    try:
        categories = Category.query.order_by(Category.name).all()
        return render_template('admin/categories.html', categories=categories, config=BUSINESS_CONFIG)
    except Exception as e:
        print(f"❌ Admin categories error: {str(e)}", file=sys.stderr)
        flash('Error loading categories.', 'danger')
        return render_template('admin/categories.html', categories=[], config=BUSINESS_CONFIG)

@app.route('/admin/categories/add', methods=['GET', 'POST'])
@admin_required
def admin_add_category():
    """Add category"""
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            description = request.form.get('description')
            slug = request.form.get('slug', '').lower().replace(' ', '-')
            
            if not slug:
                slug = name.lower().replace(' ', '-')
            
            # Check if slug already exists
            existing_category = Category.query.filter_by(slug=slug).first()
            if existing_category:
                flash('Category with this slug already exists. Please use a different slug.', 'danger')
                return redirect(url_for('admin_add_category'))
            
            category = Category(
                name=name,
                slug=slug,
                description=description
            )
            
            # Handle image upload
            if 'image' in request.files:
                image_file = request.files['image']
                if image_file and allowed_file(image_file.filename):
                    filename = secure_filename(f"{uuid.uuid4()}.{image_file.filename.split('.')[-1]}")
                    image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    image_file.save(image_path)
                    category.image_url = f"uploads/{filename}"
            
            db.session.add(category)
            db.session.commit()
            
            flash(f'Category "{name}" added successfully!', 'success')
            return redirect(url_for('admin_categories'))
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Add category error: {str(e)}", file=sys.stderr)
            flash('Error adding category. Please try again.', 'danger')
    
    return render_template('admin/add_category.html', config=BUSINESS_CONFIG)

@app.route('/admin/categories/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_category(id):
    """Edit category"""
    category = Category.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            category.name = request.form.get('name')
            category.description = request.form.get('description')
            slug = request.form.get('slug', '').lower().replace(' ', '-')
            
            if slug and slug != category.slug:
                # Check if new slug already exists
                existing_category = Category.query.filter_by(slug=slug).first()
                if existing_category and existing_category.id != id:
                    flash('Category with this slug already exists. Please use a different slug.', 'danger')
                    return redirect(url_for('admin_edit_category', id=id))
                category.slug = slug
            
            # Handle image upload
            if 'image' in request.files:
                image_file = request.files['image']
                if image_file and allowed_file(image_file.filename):
                    filename = secure_filename(f"{uuid.uuid4()}.{image_file.filename.split('.')[-1]}")
                    image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    image_file.save(image_path)
                    category.image_url = f"uploads/{filename}"
            
            db.session.commit()
            
            flash(f'Category "{category.name}" updated successfully!', 'success')
            return redirect(url_for('admin_categories'))
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Edit category error: {str(e)}", file=sys.stderr)
            flash('Error updating category. Please try again.', 'danger')
    
    return render_template('admin/edit_category.html', category=category, config=BUSINESS_CONFIG)

@app.route('/admin/categories/delete/<int:id>', methods=['POST'])
@admin_required
def admin_delete_category(id):
    """Delete category"""
    try:
        category = Category.query.get_or_404(id)
        category_name = category.name
        
        # Check if category has products
        if category.products.count() > 0:
            flash(f'Cannot delete "{category_name}" because it has products associated with it.', 'danger')
            return redirect(url_for('admin_categories'))
        
        db.session.delete(category)
        db.session.commit()
        
        flash(f'Category "{category_name}" deleted successfully!', 'success')
        return redirect(url_for('admin_categories'))
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Delete category error: {str(e)}", file=sys.stderr)
        flash('Error deleting category. Please try again.', 'danger')
        return redirect(url_for('admin_categories'))

# ========== ADMIN SETTINGS ROUTES ==========

@app.route('/admin/settings', methods=['GET', 'POST'])
@admin_required
def admin_settings():
    """Admin settings - change password"""
    if request.method == 'POST':
        try:
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            admin = User.query.get(session['admin_id'])
            
            if not admin.check_password(current_password):
                flash('Current password is incorrect', 'danger')
                return redirect(url_for('admin_settings'))
            
            if new_password != confirm_password:
                flash('New passwords do not match', 'danger')
                return redirect(url_for('admin_settings'))
            
            if len(new_password) < 6:
                flash('Password must be at least 6 characters', 'danger')
                return redirect(url_for('admin_settings'))
            
            admin.set_password(new_password)
            db.session.commit()
            
            flash('Password changed successfully!', 'success')
            return redirect(url_for('admin_settings'))
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Change password error: {str(e)}", file=sys.stderr)
            flash('Error changing password. Please try again.', 'danger')
    
    return render_template('admin/settings.html', config=BUSINESS_CONFIG)

@app.route('/admin/profile', methods=['GET', 'POST'])
@admin_required
def admin_profile():
    """Admin profile"""
    admin = User.query.get(session['admin_id'])
    
    if request.method == 'POST':
        try:
            admin.username = request.form.get('username', admin.username)
            admin.email = request.form.get('email', admin.email)
            
            db.session.commit()
            session['admin_name'] = admin.username
            
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('admin_profile'))
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Update profile error: {str(e)}", file=sys.stderr)
            flash('Error updating profile. Please try again.', 'danger')
    
    return render_template('admin/profile.html', admin=admin, config=BUSINESS_CONFIG)

# ========== ADMIN CONTACT MESSAGES ==========

@app.route('/admin/messages')
@admin_required
def admin_messages():
    """Admin contact messages"""
    try:
        messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
        return render_template('admin/messages.html', messages=messages, config=BUSINESS_CONFIG)
    except Exception as e:
        print(f"❌ Admin messages error: {str(e)}", file=sys.stderr)
        flash('Error loading messages.', 'danger')
        return render_template('admin/messages.html', messages=[], config=BUSINESS_CONFIG)

@app.route('/admin/messages/<int:id>')
@admin_required
def admin_message_detail(id):
    """Contact message detail"""
    try:
        message = ContactMessage.query.get_or_404(id)
        
        # Mark as read
        if not message.read:
            message.read = True
            db.session.commit()
        
        return render_template('admin/message_detail.html', message=message, config=BUSINESS_CONFIG)
    except Exception as e:
        print(f"❌ Admin message detail error: {str(e)}", file=sys.stderr)
        flash('Error loading message.', 'danger')
        return redirect(url_for('admin_messages'))

@app.route('/admin/messages/delete/<int:id>', methods=['POST'])
@admin_required
def admin_delete_message(id):
    """Delete contact message"""
    try:
        message = ContactMessage.query.get_or_404(id)
        db.session.delete(message)
        db.session.commit()
        
        flash('Message deleted successfully!', 'success')
        return redirect(url_for('admin_messages'))
        
    except Exception as e:
        db.session.rollback()
        flash('Error deleting message.', 'danger')
        return redirect(url_for('admin_messages'))

# ========== ADMIN INVENTORY ==========

@app.route('/admin/inventory')
@admin_required
def admin_inventory():
    """Admin inventory management"""
    try:
        status = request.args.get('status', 'all')
        
        query = Product.query
        
        if status == 'low':
            query = query.filter(Product.quantity <= 5, Product.quantity > 0)
        elif status == 'out':
            query = query.filter(Product.quantity == 0)
        elif status == 'in':
            query = query.filter(Product.quantity > 5)
        
        products = query.order_by(Product.quantity, Product.name).all()
        
        # Calculate inventory value
        inventory_value = db.session.query(
            func.sum(Product.cost_price * Product.quantity)
        ).scalar() or 0
        
        total_products = len(products)
        low_stock = Product.query.filter(Product.quantity <= 5, Product.quantity > 0).count()
        out_of_stock = Product.query.filter_by(quantity=0).count()
        in_stock = Product.query.filter(Product.quantity > 5).count()
        
        return render_template('admin/inventory.html',
                             products=products,
                             status=status,
                             inventory_value=inventory_value,
                             total_products=total_products,
                             low_stock=low_stock,
                             out_of_stock=out_of_stock,
                             in_stock=in_stock,
                             config=BUSINESS_CONFIG)
    except Exception as e:
        print(f"❌ Admin inventory error: {str(e)}", file=sys.stderr)
        flash('Error loading inventory.', 'danger')
        return render_template('admin/inventory.html',
                             products=[],
                             config=BUSINESS_CONFIG)

@app.route('/admin/inventory/update-stock/<int:id>', methods=['POST'])
@admin_required
def admin_update_stock(id):
    """Update product stock"""
    try:
        product = Product.query.get_or_404(id)
        action = request.form.get('action')
        quantity = int(request.form.get('quantity', 0))
        
        if action == 'add':
            product.quantity += quantity
            message = f'Added {quantity} units to {product.name}. New stock: {product.quantity}'
        elif action == 'remove':
            if quantity > product.quantity:
                flash(f'Cannot remove more than available stock ({product.quantity})', 'danger')
                return redirect(url_for('admin_inventory'))
            product.quantity -= quantity
            message = f'Removed {quantity} units from {product.name}. New stock: {product.quantity}'
        elif action == 'set':
            product.quantity = quantity
            message = f'Set stock for {product.name} to {quantity} units'
        
        db.session.commit()
        flash(message, 'success')
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Update stock error: {str(e)}", file=sys.stderr)
        flash('Error updating stock.', 'danger')
    
    return redirect(url_for('admin_inventory'))

# ========== STATIC FILE SERVING ==========

@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded files"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ========== HEALTH CHECK ==========
@app.route('/health')
def health_check():
    """Health check endpoint for Render"""
    try:
        db.session.execute('SELECT 1')
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': datetime.utcnow().isoformat(),
            'app': 'Nora Hair Line E-commerce',
            'version': '2.0.0'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

# ========== APPLICATION FACTORY ==========
def create_app():
    """Application factory for Gunicorn"""
    return app

# ========== MAIN ENTRY POINT ==========
if __name__ == '__main__':
    # Create required directories
    os.makedirs('static/uploads', exist_ok=True)
    os.makedirs('static/images', exist_ok=True)
    
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    print(f"\n{'='*60}", file=sys.stderr)
    print(f"🚀 NORA HAIR LINE E-COMMERCE - COMPLETE VERSION", file=sys.stderr)
    print(f"{'='*60}", file=sys.stderr)
    print(f"🌐 Local: http://localhost:{port}", file=sys.stderr)
    print(f"🛍️  Shop: /shop", file=sys.stderr)
    print(f"👑 Admin: /admin (admin/admin123)", file=sys.stderr)
    print(f"👤 Customer: /login", file=sys.stderr)
    print(f"📧 Contact: /contact", file=sys.stderr)
    print(f"ℹ️  About: /about", file=sys.stderr)
    print(f"{'='*60}", file=sys.stderr)
    print(f"✅ Features included:", file=sys.stderr)
    print(f"  1. Complete admin dashboard with statistics", file=sys.stderr)
    print(f"  2. Product management with image uploads", file=sys.stderr)
    print(f"  3. Order management with status tracking", file=sys.stderr)
    print(f"  4. Customer management", file=sys.stderr)
    print(f"  5. Review moderation", file=sys.stderr)
    print(f"  6. Category management", file=sys.stderr)
    print(f"  7. Inventory management", file=sys.stderr)
    print(f"  8. Contact message management", file=sys.stderr)
    print(f"  9. Newsletter subscription", file=sys.stderr)
    print(f"  10. File upload handling", file=sys.stderr)
    print(f"  11. API endpoints for AJAX", file=sys.stderr)
    print(f"  12. Health check endpoint", file=sys.stderr)
    print(f"{'='*60}", file=sys.stderr)
    
    app.run(host='0.0.0.0', port=port, debug=debug)

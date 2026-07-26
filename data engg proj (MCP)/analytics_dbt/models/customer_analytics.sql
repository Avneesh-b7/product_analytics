-- models/customer_analytics.sql
with customer_orders as (
  select
    c.customer_id,
    c.email,
    c.tier,
    c.country,
    c.registration_date,
    count(distinct o.order_id) as total_orders,
    coalesce(sum(o.total_amount), 0) as lifetime_value,
    min(o.order_date) as first_order_date,
    max(o.order_date) as last_order_date,
    avg(o.total_amount) as avg_order_value
  from app.customers c
  left join app.orders o on c.customer_id = o.customer_id
  group by 1, 2, 3, 4, 5
),

product_preferences as (
  select
    oi.order_id,
    o.customer_id,
    p.category,
    sum(oi.quantity * oi.price) as category_spend
  from app.order_items oi
  join app.orders o on oi.order_id = o.order_id
  join app.products p on oi.product_id = p.product_id
  group by 1, 2, 3
),

top_category_per_customer as (
  select
    customer_id,
    category,
    sum(category_spend) as total_category_spend,
    row_number() over (partition by customer_id order by sum(category_spend) desc) as category_rank
  from product_preferences
  group by 1, 2
)

select
  co.*,
  tcc.category as favorite_category,
  (current_date - co.registration_date) as days_since_registration,
  (co.last_order_date - co.first_order_date) as customer_lifespan_days,
  case
    when co.total_orders = 0 then 'inactive'
    when co.total_orders < 5 then 'occasional'
    when co.total_orders < 15 then 'regular'
    else 'vip'
  end as customer_segment
from customer_orders co
left join top_category_per_customer tcc
  on co.customer_id = tcc.customer_id
  and tcc.category_rank = 1

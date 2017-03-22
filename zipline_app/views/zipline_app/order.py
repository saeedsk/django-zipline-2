from django.views import generic
from django.utils import timezone
from django.contrib import messages
from ...models.zipline_app.order import Order
from ...utils import redirect_index_or_local
from ...widgets import AssetModelSelect2Widget, AccountModelSelect2Widget

class OrderCreate(generic.CreateView):
  model = Order
  fields = ['pub_date', 'asset', 'order_side', 'amount_unsigned', 'account', 'order_text']
  template_name = 'zipline_app/order/order_form.html'

  # override widget in createview
  # http://stackoverflow.com/a/21407374/4126114
  def get_form(self):
    form = super(OrderCreate, self).get_form()
    form.fields['asset'].widget = AssetModelSelect2Widget()
    form.fields['account'].widget = AccountModelSelect2Widget()
    return form

  def form_valid(self, form):
    order = form.save(commit=False)
    if self.request.user.is_authenticated():
      order.user = self.request.user
    return super(OrderCreate, self).form_valid(form)

  def get_success_url(self):
    # django message levels
    # https://docs.djangoproject.com/en/1.10/ref/contrib/messages/#message-levels
    messages.add_message(self.request, messages.INFO, "Successfully created order: %s" % self.object)
    return redirect_index_or_local(self,'zipline_app:orders-list')

class OrderList(generic.ListView):
  template_name = 'zipline_app/order/order_list.html'
  context_object_name='order_list'
  def get_queryset(self):
    return Order.objects.all()

  def get_context_data(self, *args, **kwargs):
    context = super(OrderList, self).get_context_data(*args, **kwargs)
    view = OrderCreate()
    form = view.get_form_class()
    context["order_form"]=form
    return context

class OrderDelete(generic.DeleteView):
  model = Order
  template_name = 'zipline_app/order/order_confirm_delete.html'
  def get_success_url(self):
    messages.add_message(self.request, messages.INFO, "Successfully deleted order: %s" % self.object)
    return redirect_index_or_local(self,'zipline_app:orders-list')

class OrderDetailView(generic.DetailView):
    model = Order
    template_name = 'zipline_app/order/order_detail.html'
    def get_queryset(self):
        """
        Excludes any orders that aren't published yet.
        """
        return Order.objects.filter(pub_date__lte=timezone.now())

class OrderUpdateView(generic.UpdateView):
  model = Order
  fields = ['pub_date', 'asset', 'order_side', 'amount_unsigned', 'account', 'order_text']
  template_name = 'zipline_app/order/order_form.html'

  def get_success_url(self):
    # django message levels
    # https://docs.djangoproject.com/en/1.10/ref/contrib/messages/#message-levels
    messages.add_message(self.request, messages.INFO, "Successfully updated order: %s" % self.object)
    return redirect_index_or_local(self,'zipline_app:orders-list')


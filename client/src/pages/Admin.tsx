import { useState, useEffect } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { useLocation } from "wouter";
import { ProductForm, type ProductFormData } from "@/components/admin/ProductForm";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";
import { Package, ShoppingCart, Users, TrendingUp, Trash2, Edit, Plus, Eye, LogOut } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { apiRequest, queryClient } from "@/lib/queryClient";
import type { Product, Order, OrderItem } from "@shared/schema";

export default function Admin() {
  const { toast } = useToast();
  const [, setLocation] = useLocation();
  const [editingProduct, setEditingProduct] = useState<Product | null>(null);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [activeTab, setActiveTab] = useState("products");
  const [viewingOrder, setViewingOrder] = useState<Order | null>(null);

  const { data: session, isLoading: sessionLoading } = useQuery<{ isAdmin: boolean }>({
    queryKey: ["/api/admin/session"],
  });

  useEffect(() => {
    if (!sessionLoading && !session?.isAdmin) {
      setLocation("/admin/login");
    }
  }, [session, sessionLoading, setLocation]);

  const logoutMutation = useMutation({
    mutationFn: async () => {
      const response = await apiRequest("POST", "/api/admin/logout");
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/admin/session"] });
      toast({ title: "Logged out successfully" });
      setLocation("/admin/login");
    },
  });

  if (sessionLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-pulse text-lg">Loading...</div>
      </div>
    );
  }

  if (!session?.isAdmin) {
    return null;
  }

  const { data: products = [], isLoading: productsLoading } = useQuery<Product[]>({
    queryKey: ["/api/products"],
  });

  const { data: orders = [], isLoading: ordersLoading } = useQuery<Order[]>({
    queryKey: ["/api/orders"],
  });

  const addProductMutation = useMutation({
    mutationFn: async (data: ProductFormData) => {
      const productData = {
        ...data,
        images: data.images.split("\n").filter((url) => url.trim()),
        inStock: data.stockCount > 0,
      };
      const response = await apiRequest("POST", "/api/products", productData);
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/products"] });
      toast({
        title: "Product added",
        description: "The product has been added successfully.",
      });
      setActiveTab("products");
    },
    onError: () => {
      toast({
        title: "Failed to add product",
        description: "Please try again.",
        variant: "destructive",
      });
    },
  });

  const updateProductMutation = useMutation({
    mutationFn: async ({ id, data }: { id: string; data: ProductFormData }) => {
      const productData = {
        ...data,
        images: data.images.split("\n").filter((url) => url.trim()),
        inStock: data.stockCount > 0,
      };
      const response = await apiRequest("PATCH", `/api/products/${id}`, productData);
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/products"] });
      toast({
        title: "Product updated",
        description: "The product has been updated successfully.",
      });
      setIsEditDialogOpen(false);
      setEditingProduct(null);
    },
    onError: () => {
      toast({
        title: "Failed to update product",
        description: "Please try again.",
        variant: "destructive",
      });
    },
  });

  const deleteProductMutation = useMutation({
    mutationFn: async (productId: string) => {
      await apiRequest("DELETE", `/api/products/${productId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/products"] });
      toast({
        title: "Product deleted",
        description: "The product has been removed.",
      });
    },
  });

  const updateOrderStatusMutation = useMutation({
    mutationFn: async ({ id, status }: { id: string; status: string }) => {
      const response = await apiRequest("PATCH", `/api/orders/${id}/status`, { status });
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/orders"] });
      toast({
        title: "Order updated",
        description: "Order status has been updated.",
      });
    },
  });

  const handleEditProduct = (product: Product) => {
    setEditingProduct(product);
    setIsEditDialogOpen(true);
  };

  const handleUpdateProduct = (data: ProductFormData) => {
    if (editingProduct) {
      updateProductMutation.mutate({ id: editingProduct.id, data });
    }
  };

  const totalRevenue = orders.reduce((sum, order) => sum + order.totalAmount, 0);
  const pendingOrders = orders.filter((o) => o.orderStatus === "pending").length;
  const installmentOrders = orders.filter((o) => o.paymentPlan === "installment").length;

  const getOrderItems = (order: Order): OrderItem[] => {
    try {
      return JSON.parse(order.items);
    } catch {
      return [];
    }
  };

  return (
    <main className="max-w-7xl mx-auto px-4 py-8">
      <div className="mb-8 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="font-serif text-3xl font-bold mb-2">Admin Dashboard</h1>
          <p className="text-muted-foreground">Manage your products and orders</p>
        </div>
        <Button 
          variant="outline" 
          onClick={() => logoutMutation.mutate()}
          disabled={logoutMutation.isPending}
          data-testid="button-logout"
        >
          <LogOut className="h-4 w-4 mr-2" />
          Logout
        </Button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center gap-4">
              <div className="rounded-full bg-primary/10 p-3">
                <Package className="h-6 w-6 text-primary" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Total Products</p>
                <p className="text-2xl font-bold">{products.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center gap-4">
              <div className="rounded-full bg-primary/10 p-3">
                <ShoppingCart className="h-6 w-6 text-primary" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Total Orders</p>
                <p className="text-2xl font-bold">{orders.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center gap-4">
              <div className="rounded-full bg-orange-500/10 p-3">
                <Users className="h-6 w-6 text-orange-500" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Pending Orders</p>
                <p className="text-2xl font-bold">{pendingOrders}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center gap-4">
              <div className="rounded-full bg-green-500/10 p-3">
                <TrendingUp className="h-6 w-6 text-green-500" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Total Revenue</p>
                <p className="text-2xl font-bold">N{totalRevenue.toLocaleString()}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList>
          <TabsTrigger value="products" data-testid="tab-products">Products</TabsTrigger>
          <TabsTrigger value="add-product" data-testid="tab-add-product">
            <Plus className="h-4 w-4 mr-1" />
            Add Product
          </TabsTrigger>
          <TabsTrigger value="orders" data-testid="tab-orders">
            Orders
            {pendingOrders > 0 && (
              <Badge variant="destructive" className="ml-2">{pendingOrders}</Badge>
            )}
          </TabsTrigger>
        </TabsList>

        <TabsContent value="products" className="mt-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between gap-2">
              <CardTitle>All Products ({products.length})</CardTitle>
              <Button onClick={() => setActiveTab("add-product")} data-testid="button-add-new">
                <Plus className="h-4 w-4 mr-2" />
                Add New
              </Button>
            </CardHeader>
            <CardContent>
              {productsLoading ? (
                <div className="space-y-4">
                  {[...Array(5)].map((_, i) => (
                    <Skeleton key={i} className="h-12 w-full" />
                  ))}
                </div>
              ) : products.length === 0 ? (
                <div className="text-center py-12">
                  <Package className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                  <p className="text-muted-foreground mb-4">
                    No products yet. Add your first product!
                  </p>
                  <Button onClick={() => setActiveTab("add-product")}>
                    <Plus className="h-4 w-4 mr-2" />
                    Add Product
                  </Button>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Product</TableHead>
                      <TableHead>Category</TableHead>
                      <TableHead>Price</TableHead>
                      <TableHead>Stock</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {products.map((product) => (
                      <TableRow key={product.id} data-testid={`row-product-${product.id}`}>
                        <TableCell className="font-medium">
                          <div className="flex items-center gap-3">
                            <img
                              src={product.images[0] || "/placeholder.jpg"}
                              alt={product.name}
                              className="w-10 h-10 rounded object-cover"
                            />
                            <div>
                              <span className="truncate max-w-[200px] block">{product.name}</span>
                              {product.featured && (
                                <Badge variant="secondary" className="text-xs mt-1">Featured</Badge>
                              )}
                            </div>
                          </div>
                        </TableCell>
                        <TableCell className="capitalize">{product.category.replace("-", " ")}</TableCell>
                        <TableCell>N{product.price.toLocaleString()}</TableCell>
                        <TableCell>{product.stockCount}</TableCell>
                        <TableCell>
                          <Badge variant={product.inStock ? "default" : "secondary"}>
                            {product.inStock ? "In Stock" : "Out of Stock"}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex items-center justify-end gap-1">
                            <Button
                              size="icon"
                              variant="ghost"
                              onClick={() => handleEditProduct(product)}
                              data-testid={`button-edit-${product.id}`}
                            >
                              <Edit className="h-4 w-4" />
                            </Button>
                            <Button
                              size="icon"
                              variant="ghost"
                              className="text-destructive"
                              onClick={() => deleteProductMutation.mutate(product.id)}
                              data-testid={`button-delete-${product.id}`}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="add-product" className="mt-6">
          <div className="max-w-2xl">
            <ProductForm
              onSubmit={(data) => addProductMutation.mutate(data)}
              isLoading={addProductMutation.isPending}
              mode="add"
            />
          </div>
        </TabsContent>

        <TabsContent value="orders" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                All Orders
                <Badge variant="outline">{orders.length} total</Badge>
                {installmentOrders > 0 && (
                  <Badge variant="secondary">{installmentOrders} installment</Badge>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {ordersLoading ? (
                <div className="space-y-4">
                  {[...Array(5)].map((_, i) => (
                    <Skeleton key={i} className="h-12 w-full" />
                  ))}
                </div>
              ) : orders.length === 0 ? (
                <div className="text-center py-12">
                  <ShoppingCart className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                  <p className="text-muted-foreground">No orders yet.</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Order ID</TableHead>
                      <TableHead>Date</TableHead>
                      <TableHead>Items</TableHead>
                      <TableHead>Total</TableHead>
                      <TableHead>Payment</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {orders.map((order) => {
                      const orderItems = getOrderItems(order);
                      return (
                        <TableRow key={order.id} data-testid={`row-order-${order.id}`}>
                          <TableCell className="font-mono font-medium">
                            {order.id.slice(0, 8).toUpperCase()}
                          </TableCell>
                          <TableCell>
                            {new Date(order.orderDate).toLocaleDateString()}
                          </TableCell>
                          <TableCell>
                            {orderItems.length} item{orderItems.length !== 1 ? "s" : ""}
                          </TableCell>
                          <TableCell className="font-medium">
                            N{order.totalAmount.toLocaleString()}
                          </TableCell>
                          <TableCell>
                            <Badge variant={order.paymentPlan === "installment" ? "default" : "secondary"}>
                              {order.paymentPlan === "installment" ? "Installment" : "Full"}
                            </Badge>
                            {order.paymentPlan === "installment" && (
                              <div className="text-xs text-muted-foreground mt-1">
                                1st: N{order.firstPayment?.toLocaleString()}
                              </div>
                            )}
                          </TableCell>
                          <TableCell>
                            <Badge 
                              variant={
                                order.orderStatus === "delivered" ? "default" :
                                order.orderStatus === "shipped" ? "secondary" :
                                "outline"
                              } 
                              className="capitalize"
                            >
                              {order.orderStatus}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-right">
                            <div className="flex items-center justify-end gap-1">
                              <Button
                                size="icon"
                                variant="ghost"
                                onClick={() => setViewingOrder(order)}
                                data-testid={`button-view-${order.id}`}
                              >
                                <Eye className="h-4 w-4" />
                              </Button>
                            </div>
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Edit Product</DialogTitle>
          </DialogHeader>
          {editingProduct && (
            <ProductForm
              onSubmit={handleUpdateProduct}
              isLoading={updateProductMutation.isPending}
              mode="edit"
              defaultValues={{
                name: editingProduct.name,
                description: editingProduct.description,
                price: editingProduct.price,
                category: editingProduct.category,
                length: editingProduct.length || "",
                texture: editingProduct.texture || "",
                images: editingProduct.images.join("\n"),
                stockCount: editingProduct.stockCount || 0,
                featured: editingProduct.featured || false,
                badge: editingProduct.badge || "",
              }}
            />
          )}
        </DialogContent>
      </Dialog>

      <Dialog open={!!viewingOrder} onOpenChange={() => setViewingOrder(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Order Details</DialogTitle>
          </DialogHeader>
          {viewingOrder && (
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-muted-foreground">Order ID:</span>
                <span className="font-mono font-bold">{viewingOrder.id.slice(0, 8).toUpperCase()}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-muted-foreground">Date:</span>
                <span>{new Date(viewingOrder.orderDate).toLocaleString()}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-muted-foreground">Payment Plan:</span>
                <Badge>{viewingOrder.paymentPlan}</Badge>
              </div>
              {viewingOrder.paymentPlan === "installment" && (
                <>
                  <div className="flex justify-between items-center">
                    <span className="text-muted-foreground">First Payment:</span>
                    <span>N{viewingOrder.firstPayment?.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-muted-foreground">Second Payment:</span>
                    <span>N{viewingOrder.secondPayment?.toLocaleString()}</span>
                  </div>
                </>
              )}
              <div className="flex justify-between items-center">
                <span className="text-muted-foreground">Total:</span>
                <span className="font-bold text-lg">N{viewingOrder.totalAmount.toLocaleString()}</span>
              </div>
              <div className="border-t pt-4 space-y-2">
                <p className="font-medium">Items:</p>
                {getOrderItems(viewingOrder).map((item, idx) => (
                  <div key={idx} className="flex justify-between text-sm">
                    <span>{item.quantity}x {item.productName}</span>
                    <span>N{(item.price * item.quantity).toLocaleString()}</span>
                  </div>
                ))}
              </div>
              <div className="border-t pt-4">
                <p className="text-sm text-muted-foreground mb-2">Update Status:</p>
                <div className="flex flex-wrap gap-2">
                  {["pending", "processing", "shipped", "delivered"].map((status) => (
                    <Button
                      key={status}
                      size="sm"
                      variant={viewingOrder.orderStatus === status ? "default" : "outline"}
                      onClick={() => updateOrderStatusMutation.mutate({ id: viewingOrder.id, status })}
                      disabled={updateOrderStatusMutation.isPending}
                      className="capitalize"
                    >
                      {status}
                    </Button>
                  ))}
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </main>
  );
}

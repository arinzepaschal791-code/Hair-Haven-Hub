import { useState, useRef } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
  FormDescription,
} from "@/components/ui/form";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Package, Save, Plus, Upload, X, Image, Video, Loader2 } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

const productSchema = z.object({
  name: z.string().min(3, "Product name must be at least 3 characters"),
  description: z.string().min(10, "Description must be at least 10 characters"),
  price: z.number().min(1000, "Price must be at least 1000"),
  category: z.string().min(1, "Category is required"),
  length: z.string().optional(),
  texture: z.string().optional(),
  images: z.string().min(1, "At least one image is required"),
  video: z.string().optional(),
  stockCount: z.number().min(0, "Stock count must be 0 or more"),
  featured: z.boolean().default(false),
  badge: z.string().optional(),
});

export type ProductFormData = z.infer<typeof productSchema>;

interface ProductFormProps {
  onSubmit: (data: ProductFormData) => void;
  isLoading?: boolean;
  defaultValues?: Partial<ProductFormData>;
  mode?: "add" | "edit";
}

export function ProductForm({ onSubmit, isLoading, defaultValues, mode = "add" }: ProductFormProps) {
  const { toast } = useToast();
  const [uploadedImages, setUploadedImages] = useState<string[]>(
    defaultValues?.images ? defaultValues.images.split("\n").filter(Boolean) : []
  );
  const [uploadedVideo, setUploadedVideo] = useState<string>(defaultValues?.video || "");
  const [isUploadingImages, setIsUploadingImages] = useState(false);
  const [isUploadingVideo, setIsUploadingVideo] = useState(false);
  const imageInputRef = useRef<HTMLInputElement>(null);
  const videoInputRef = useRef<HTMLInputElement>(null);

  const form = useForm<ProductFormData>({
    resolver: zodResolver(productSchema),
    defaultValues: {
      name: "",
      description: "",
      price: 0,
      category: "",
      length: "",
      texture: "",
      images: defaultValues?.images || "",
      video: "",
      stockCount: 10,
      featured: false,
      badge: "",
      ...defaultValues,
    },
  });

  const handleImageUpload = async (files: FileList | null) => {
    if (!files || files.length === 0) return;

    setIsUploadingImages(true);
    const newUrls: string[] = [];

    try {
      for (const file of Array.from(files)) {
        // Step 1: Request presigned URL from backend
        const urlResponse = await fetch("/api/uploads/request-url", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({
            name: file.name,
            size: file.size,
            contentType: file.type,
          }),
        });

        if (!urlResponse.ok) {
          throw new Error("Failed to get upload URL");
        }

        const { uploadURL, objectPath } = await urlResponse.json();

        // Step 2: Upload file directly to cloud storage
        const uploadResponse = await fetch(uploadURL, {
          method: "PUT",
          body: file,
          headers: { "Content-Type": file.type },
        });

        if (!uploadResponse.ok) {
          throw new Error("Upload failed");
        }

        // Use the object path for permanent storage URL
        newUrls.push(objectPath);
      }

      const allImages = [...uploadedImages, ...newUrls];
      setUploadedImages(allImages);
      form.setValue("images", allImages.join("\n"));
      toast({
        title: "Images uploaded",
        description: `${newUrls.length} image(s) uploaded permanently.`,
      });
    } catch (error) {
      toast({
        title: "Upload failed",
        description: "Failed to upload images. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsUploadingImages(false);
    }
  };

  const handleVideoUpload = async (files: FileList | null) => {
    if (!files || files.length === 0) return;

    setIsUploadingVideo(true);

    try {
      const file = files[0];
      
      // Step 1: Request presigned URL from backend
      const urlResponse = await fetch("/api/uploads/request-url", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          name: file.name,
          size: file.size,
          contentType: file.type,
        }),
      });

      if (!urlResponse.ok) {
        throw new Error("Failed to get upload URL");
      }

      const { uploadURL, objectPath } = await urlResponse.json();

      // Step 2: Upload file directly to cloud storage
      const uploadResponse = await fetch(uploadURL, {
        method: "PUT",
        body: file,
        headers: { "Content-Type": file.type },
      });

      if (!uploadResponse.ok) {
        throw new Error("Upload failed");
      }

      setUploadedVideo(objectPath);
      form.setValue("video", objectPath);
      toast({
        title: "Video uploaded",
        description: "Video uploaded permanently.",
      });
    } catch (error) {
      toast({
        title: "Upload failed",
        description: "Failed to upload video. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsUploadingVideo(false);
    }
  };

  const removeImage = (index: number) => {
    const newImages = uploadedImages.filter((_, i) => i !== index);
    setUploadedImages(newImages);
    form.setValue("images", newImages.join("\n"));
  };

  const removeVideo = () => {
    setUploadedVideo("");
    form.setValue("video", "");
  };

  const handleSubmit = (data: ProductFormData) => {
    onSubmit(data);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          {mode === "add" ? <Plus className="h-5 w-5" /> : <Package className="h-5 w-5" />}
          {mode === "add" ? "Add New Product" : "Edit Product"}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-6">
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Product Name</FormLabel>
                  <FormControl>
                    <Input placeholder="e.g., Bone Straight Hair 22 inches" {...field} data-testid="input-product-name" />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="description"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Description</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="Describe the product..."
                      className="min-h-24"
                      {...field}
                      data-testid="input-product-description"
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="price"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Price (NGN)</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        placeholder="e.g., 120000"
                        {...field}
                        onChange={(e) => field.onChange(Number(e.target.value))}
                        data-testid="input-product-price"
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="category"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Category</FormLabel>
                    <Select onValueChange={field.onChange} value={field.value}>
                      <FormControl>
                        <SelectTrigger data-testid="select-product-category">
                          <SelectValue placeholder="Select category" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="bone-straight">Bone Straight</SelectItem>
                        <SelectItem value="wig">Wigs</SelectItem>
                        <SelectItem value="hair-care">Hair Care</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="length"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Length (Optional)</FormLabel>
                    <Select onValueChange={field.onChange} value={field.value}>
                      <FormControl>
                        <SelectTrigger data-testid="select-product-length">
                          <SelectValue placeholder="Select length" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="10 inches">10 inches</SelectItem>
                        <SelectItem value="12 inches">12 inches</SelectItem>
                        <SelectItem value="14 inches">14 inches</SelectItem>
                        <SelectItem value="16 inches">16 inches</SelectItem>
                        <SelectItem value="18 inches">18 inches</SelectItem>
                        <SelectItem value="20 inches">20 inches</SelectItem>
                        <SelectItem value="22 inches">22 inches</SelectItem>
                        <SelectItem value="24 inches">24 inches</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="texture"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Texture (Optional)</FormLabel>
                    <Select onValueChange={field.onChange} value={field.value}>
                      <FormControl>
                        <SelectTrigger data-testid="select-product-texture">
                          <SelectValue placeholder="Select texture" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="straight">Straight</SelectItem>
                        <SelectItem value="body-wave">Body Wave</SelectItem>
                        <SelectItem value="deep-wave">Deep Wave</SelectItem>
                        <SelectItem value="curly">Curly</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <FormField
              control={form.control}
              name="images"
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="flex items-center gap-2">
                    <Image className="h-4 w-4" />
                    Product Images
                  </FormLabel>
                  <div className="space-y-4">
                    <div
                      className="border-2 border-dashed rounded-lg p-6 text-center cursor-pointer hover:border-primary/50 transition-colors"
                      onClick={() => imageInputRef.current?.click()}
                    >
                      <input
                        ref={imageInputRef}
                        type="file"
                        accept="image/*"
                        multiple
                        className="hidden"
                        onChange={(e) => handleImageUpload(e.target.files)}
                        data-testid="input-image-upload"
                      />
                      {isUploadingImages ? (
                        <div className="flex flex-col items-center gap-2">
                          <Loader2 className="h-8 w-8 animate-spin text-primary" />
                          <p className="text-sm text-muted-foreground">Uploading...</p>
                        </div>
                      ) : (
                        <div className="flex flex-col items-center gap-2">
                          <Upload className="h-8 w-8 text-muted-foreground" />
                          <p className="text-sm font-medium">Click to upload images</p>
                          <p className="text-xs text-muted-foreground">PNG, JPG, GIF, WEBP up to 10MB each</p>
                        </div>
                      )}
                    </div>

                    {uploadedImages.length > 0 && (
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                        {uploadedImages.map((url, index) => (
                          <div key={index} className="relative group">
                            <img
                              src={url}
                              alt={`Product ${index + 1}`}
                              className="w-full aspect-square object-cover rounded-md border"
                            />
                            {index === 0 && (
                              <Badge className="absolute top-1 left-1 text-xs">Main</Badge>
                            )}
                            <Button
                              type="button"
                              size="icon"
                              variant="destructive"
                              className="absolute top-1 right-1 h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity"
                              onClick={() => removeImage(index)}
                            >
                              <X className="h-3 w-3" />
                            </Button>
                          </div>
                        ))}
                      </div>
                    )}

                    <div>
                      <FormDescription className="mb-2">
                        Or enter image URLs manually (one per line):
                      </FormDescription>
                      <Textarea
                        placeholder="https://example.com/image1.jpg"
                        value={field.value}
                        onChange={(e) => {
                          field.onChange(e.target.value);
                          setUploadedImages(e.target.value.split("\n").filter(Boolean));
                        }}
                        data-testid="input-product-images"
                      />
                    </div>
                  </div>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="video"
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="flex items-center gap-2">
                    <Video className="h-4 w-4" />
                    Product Video (Optional)
                  </FormLabel>
                  <div className="space-y-4">
                    {uploadedVideo ? (
                      <div className="relative">
                        <video
                          src={uploadedVideo}
                          className="w-full max-w-md rounded-md border"
                          controls
                        />
                        <Button
                          type="button"
                          size="icon"
                          variant="destructive"
                          className="absolute top-2 right-2"
                          onClick={removeVideo}
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      </div>
                    ) : (
                      <div
                        className="border-2 border-dashed rounded-lg p-6 text-center cursor-pointer hover:border-primary/50 transition-colors"
                        onClick={() => videoInputRef.current?.click()}
                      >
                        <input
                          ref={videoInputRef}
                          type="file"
                          accept="video/*"
                          className="hidden"
                          onChange={(e) => handleVideoUpload(e.target.files)}
                          data-testid="input-video-upload"
                        />
                        {isUploadingVideo ? (
                          <div className="flex flex-col items-center gap-2">
                            <Loader2 className="h-8 w-8 animate-spin text-primary" />
                            <p className="text-sm text-muted-foreground">Uploading video...</p>
                          </div>
                        ) : (
                          <div className="flex flex-col items-center gap-2">
                            <Video className="h-8 w-8 text-muted-foreground" />
                            <p className="text-sm font-medium">Click to upload video</p>
                            <p className="text-xs text-muted-foreground">MP4, WEBM, MOV up to 100MB</p>
                          </div>
                        )}
                      </div>
                    )}

                    <div>
                      <FormDescription className="mb-2">
                        Or enter video URL:
                      </FormDescription>
                      <Input
                        placeholder="https://example.com/video.mp4"
                        value={field.value}
                        onChange={(e) => {
                          field.onChange(e.target.value);
                          setUploadedVideo(e.target.value);
                        }}
                        data-testid="input-product-video-url"
                      />
                    </div>
                  </div>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="stockCount"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Stock Count</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        placeholder="e.g., 10"
                        {...field}
                        onChange={(e) => field.onChange(Number(e.target.value))}
                        data-testid="input-product-stock"
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="badge"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Badge (Optional)</FormLabel>
                    <Select onValueChange={field.onChange} value={field.value}>
                      <FormControl>
                        <SelectTrigger data-testid="select-product-badge">
                          <SelectValue placeholder="Select badge" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="none">None</SelectItem>
                        <SelectItem value="New">New</SelectItem>
                        <SelectItem value="Sale">Sale</SelectItem>
                        <SelectItem value="Best Seller">Best Seller</SelectItem>
                        <SelectItem value="Premium">Premium</SelectItem>
                        <SelectItem value="Limited">Limited</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <FormField
              control={form.control}
              name="featured"
              render={({ field }) => (
                <FormItem className="flex flex-row items-start gap-3 space-y-0">
                  <FormControl>
                    <Checkbox
                      checked={field.value}
                      onCheckedChange={field.onChange}
                      data-testid="checkbox-featured"
                    />
                  </FormControl>
                  <div className="space-y-1 leading-none">
                    <FormLabel className="cursor-pointer">Featured Product</FormLabel>
                    <FormDescription>
                      Featured products appear on the homepage
                    </FormDescription>
                  </div>
                </FormItem>
              )}
            />

            <Button type="submit" className="w-full" size="lg" disabled={isLoading || isUploadingImages || isUploadingVideo} data-testid="button-save-product">
              <Save className="h-5 w-5 mr-2" />
              {isLoading ? "Saving..." : mode === "add" ? "Add Product" : "Update Product"}
            </Button>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
}

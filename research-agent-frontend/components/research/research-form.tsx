'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { ChevronDown, Search } from 'lucide-react';

import { Button } from '@/components/ui/button';
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

const formSchema = z.object({
  query: z.string().min(3, 'Query must be at least 3 characters').max(500),
  depth: z.enum(['quick', 'standard', 'comprehensive']),
  max_sources: z.number().min(5).max(50),
  include_pdfs: z.boolean(),
  include_academic: z.boolean(),
  custom_instructions: z.string().max(1000).optional(),
});

type FormValues = z.infer<typeof formSchema>;

interface ResearchFormProps {
  onSubmit: (values: FormValues) => void;
  isLoading?: boolean;
}

export function ResearchForm({ onSubmit, isLoading }: ResearchFormProps) {
  const [showAdvanced, setShowAdvanced] = useState(false);

  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      query: '',
      depth: 'standard',
      max_sources: 20,
      include_pdfs: true,
      include_academic: false,
      custom_instructions: '',
    },
  });

  const handleSubmit = (values: FormValues) => {
    onSubmit(values);
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>Start New Research</CardTitle>
        <CardDescription>
          Enter your research query and configure the search parameters
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-6">
            <FormField
              control={form.control}
              name="query"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Research Query</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="What would you like to research? Be specific for better results..."
                      className="min-h-[100px]"
                      {...field}
                    />
                  </FormControl>
                  <FormDescription>
                    Describe what you want to research in detail
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="depth"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Research Depth</FormLabel>
                  <Select onValueChange={field.onChange} defaultValue={field.value}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Select research depth" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="quick">
                        <div>
                          <div className="font-medium">Quick</div>
                          <div className="text-sm text-muted-foreground">
                            Fast research with 5-10 sources (~1 min)
                          </div>
                        </div>
                      </SelectItem>
                      <SelectItem value="standard">
                        <div>
                          <div className="font-medium">Standard</div>
                          <div className="text-sm text-muted-foreground">
                            Balanced research with 10-20 sources (~2-3 min)
                          </div>
                        </div>
                      </SelectItem>
                      <SelectItem value="comprehensive">
                        <div>
                          <div className="font-medium">Comprehensive</div>
                          <div className="text-sm text-muted-foreground">
                            Thorough research with 20-50 sources (~5-10 min)
                          </div>
                        </div>
                      </SelectItem>
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            <Collapsible open={showAdvanced} onOpenChange={setShowAdvanced}>
              <CollapsibleTrigger asChild>
                <Button variant="ghost" type="button" className="w-full justify-between">
                  Advanced Options
                  <ChevronDown
                    className={`h-4 w-4 transition-transform ${
                      showAdvanced ? 'rotate-180' : ''
                    }`}
                  />
                </Button>
              </CollapsibleTrigger>
              <CollapsibleContent className="space-y-4 pt-4">
                <FormField
                  control={form.control}
                  name="max_sources"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Maximum Sources: {field.value}</FormLabel>
                      <FormControl>
                        <Slider
                          min={5}
                          max={50}
                          step={5}
                          value={[field.value]}
                          onValueChange={(value) => field.onChange(value[0])}
                        />
                      </FormControl>
                      <FormDescription>
                        Number of sources to analyze
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <div className="space-y-3">
                  <FormField
                    control={form.control}
                    name="include_pdfs"
                    render={({ field }) => (
                      <FormItem className="flex flex-row items-start space-x-3 space-y-0">
                        <FormControl>
                          <Checkbox
                            checked={field.value}
                            onCheckedChange={field.onChange}
                          />
                        </FormControl>
                        <div className="space-y-1 leading-none">
                          <FormLabel>Include PDFs</FormLabel>
                          <FormDescription>
                            Extract and analyze content from PDF documents
                          </FormDescription>
                        </div>
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="include_academic"
                    render={({ field }) => (
                      <FormItem className="flex flex-row items-start space-x-3 space-y-0">
                        <FormControl>
                          <Checkbox
                            checked={field.value}
                            onCheckedChange={field.onChange}
                          />
                        </FormControl>
                        <div className="space-y-1 leading-none">
                          <FormLabel>Include Academic Sources</FormLabel>
                          <FormDescription>
                            Search academic papers and journals
                          </FormDescription>
                        </div>
                      </FormItem>
                    )}
                  />
                </div>

                <FormField
                  control={form.control}
                  name="custom_instructions"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Custom Instructions (Optional)</FormLabel>
                      <FormControl>
                        <Textarea
                          placeholder="Any specific requirements or focus areas for the research..."
                          {...field}
                        />
                      </FormControl>
                      <FormDescription>
                        Additional guidance for the research
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </CollapsibleContent>
            </Collapsible>

            <Button type="submit" className="w-full" size="lg" disabled={isLoading}>
              {isLoading ? (
                <>
                  <span className="animate-spin mr-2">⏳</span>
                  Starting Research...
                </>
              ) : (
                <>
                  <Search className="mr-2 h-4 w-4" />
                  Start Research
                </>
              )}
            </Button>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
}
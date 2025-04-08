export type FullTable = {
  id: number;
  name: string;
  suppliers: number[];
  consumers: number[];
  price_matrix: number[][];
  restrictions: Record<string, string>;
  capacities: Capacity[];
  user_id: number;
};
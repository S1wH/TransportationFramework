export type Restriction = {
    cell: [number, number]
    operator: '>' | '<'
    value: number
}
  
export type Capacity = {
    cell: [number, number]
    value: number
}
  
export type TableCell = {
    value: number | null
    coordinates: [number, number]
}
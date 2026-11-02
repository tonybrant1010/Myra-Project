import { useWindowDimensions } from "react-native";

export function gameBoardSize(width: number, height: number, reservedHeight: number): number {
  return Math.floor(Math.max(96, Math.min(560, Math.max(96, width - 32), Math.max(180, height - reservedHeight))));
}

export function useGameBoardSize(reservedHeight: number): number {
  const { width, height } = useWindowDimensions();
  return gameBoardSize(width, height, reservedHeight);
}

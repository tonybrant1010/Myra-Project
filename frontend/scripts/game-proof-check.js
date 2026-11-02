const fs = require("node:fs");
const path = require("node:path");
const ts = require("typescript");

async function fixture(seed) {
  const source = fs.readFileSync(path.join(__dirname, "../app/relax-match.tsx"), "utf8");
  const randomSource = fs.readFileSync(path.join(__dirname, "../src/utils/crypto.ts"), "utf8");
  const random = randomSource.slice(randomSource.indexOf("export function seededRandom")).replace("export ", "");
  const helpers = source.slice(source.indexOf("  const findMatches"), source.indexOf("export default function"));
  const initial = source.slice(source.indexOf("    let newBoard: string[][]"), source.indexOf("    setBoard(newBoard)"));
  const cascade = source.slice(source.indexOf("    let boardCopy =", source.indexOf("  const animateCascade")), source.indexOf("    if (!hasValidMoves(boardCopy)"));
  const code = `
    ${random}
    const GRID_SIZE = 6;
    const EMOJIS = ["🌸", "💎", "🍀", "☀️", "💧", "⭐"];
    ${helpers}
    const rng = seededRandom(seed);
    const getRandomEmoji = () => EMOJIS[Math.floor(rng() * 6)];
    ${initial}
    const original = newBoard.map(row => row.map(cell => EMOJIS.indexOf(cell)));
    let score = 0;
    const sleep = async () => {};
    const setBoard = () => {};
    const setCombo = () => {};
    const setScore = value => { score = value; };
    const Haptics = {};
    const Vibration = { vibrate() {} };
    async function runCascade(currentBoard, initialCombo = 1) {
      ${cascade}
      return boardCopy;
    }
    let board = newBoard;
    const moves = [];
    for (let turn = 0; turn < 30; turn++) {
      let chosen = null;
      for (let r = 0; r < 6 && !chosen; r++) for (let c = 0; c < 6 && !chosen; c++) {
        for (const [rr, cc] of [[r+1,c], [r,c+1]]) {
          if (rr < 6 && cc < 6 && findMatches(performSwap(board,r,c,rr,cc)).size) {
            chosen = [r,c,rr,cc]; break;
          }
        }
      }
      if (!chosen) throw Error('No playable move');
      moves.push(chosen);
      board = await runCascade(performSwap(board, ...chosen));
      if (!hasValidMoves(board)) board = shuffleBoardUntilValid(board, rng);
    }
    return { seed, original, moves, score };
  `;
  const compiled = ts.transpileModule(code, { compilerOptions: { target: ts.ScriptTarget.ES2020 } }).outputText;
  const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor;
  return new AsyncFunction("seed", compiled)(seed);
}

if (require.main === module) {
  Promise.all([1, 42, 123456, 4294967295].map(fixture))
    .then(result => process.stdout.write(JSON.stringify(result)))
    .catch(error => { console.error(error); process.exitCode = 1; });
}

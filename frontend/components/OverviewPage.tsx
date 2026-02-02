'use client';

import { useEffect, useState, useMemo } from 'react';
import { fetchFearGreedIndex, fetchMarketOverview, FearGreedData, MarketOverview } from '@/lib/api';
import FearGreedGauge from './FearGreedGauge';
import {
    TrendingUp,
    TrendingDown,
    Activity,
    Flame,
    ChevronRight,
    RefreshCw,
    ArrowUp,
    ArrowDown,
    BarChart2,
    Coins,
    Globe,
    Zap
} from 'lucide-react';

// Coin data with real logos from CoinGecko CDN - expanded for top 50 coins
const coinData: Record<string, { logo: string; color: string; name: string }> = {
    BTC: { logo: 'https://assets.coingecko.com/coins/images/1/small/bitcoin.png', color: '#f7931a', name: 'Bitcoin' },
    ETH: { logo: 'https://assets.coingecko.com/coins/images/279/small/ethereum.png', color: '#627eea', name: 'Ethereum' },
    BNB: { logo: 'https://assets.coingecko.com/coins/images/825/small/bnb-icon2_2x.png', color: '#f3ba2f', name: 'BNB' },
    SOL: { logo: 'https://assets.coingecko.com/coins/images/4128/small/solana.png', color: '#9945ff', name: 'Solana' },
    XRP: { logo: 'https://assets.coingecko.com/coins/images/44/small/xrp-symbol-white-128.png', color: '#ffffff', name: 'XRP' },
    ADA: { logo: 'https://assets.coingecko.com/coins/images/975/small/cardano.png', color: '#0033ad', name: 'Cardano' },
    DOGE: { logo: 'https://assets.coingecko.com/coins/images/5/small/dogecoin.png', color: '#c3a634', name: 'Dogecoin' },
    AVAX: { logo: 'https://assets.coingecko.com/coins/images/12559/small/Avalanche_Circle_RedWhite_Trans.png', color: '#e84142', name: 'Avalanche' },
    LINK: { logo: 'https://assets.coingecko.com/coins/images/877/small/chainlink-new-logo.png', color: '#2a5ada', name: 'Chainlink' },
    DOT: { logo: 'https://assets.coingecko.com/coins/images/12171/small/polkadot.png', color: '#e6007a', name: 'Polkadot' },
    MATIC: { logo: 'https://assets.coingecko.com/coins/images/4713/small/matic-token-icon.png', color: '#8247e5', name: 'Polygon' },
    POL: { logo: 'https://assets.coingecko.com/coins/images/4713/small/matic-token-icon.png', color: '#8247e5', name: 'Polygon' },
    SHIB: { logo: 'https://assets.coingecko.com/coins/images/11939/small/shiba.png', color: '#ffa409', name: 'Shiba Inu' },
    TRX: { logo: 'https://assets.coingecko.com/coins/images/1094/small/tron-logo.png', color: '#ff0013', name: 'TRON' },
    UNI: { logo: 'https://assets.coingecko.com/coins/images/12504/small/uniswap-uni.png', color: '#ff007a', name: 'Uniswap' },
    ATOM: { logo: 'https://assets.coingecko.com/coins/images/1481/small/cosmos_hub.png', color: '#2e3148', name: 'Cosmos' },
    LTC: { logo: 'https://assets.coingecko.com/coins/images/2/small/litecoin.png', color: '#bfbbbb', name: 'Litecoin' },
    ETC: { logo: 'https://assets.coingecko.com/coins/images/453/small/ethereum-classic-logo.png', color: '#328332', name: 'Ethereum Classic' },
    XLM: { logo: 'https://assets.coingecko.com/coins/images/100/small/Stellar_symbol_black_RGB.png', color: '#14b6e7', name: 'Stellar' },
    BCH: { logo: 'https://assets.coingecko.com/coins/images/780/small/bitcoin-cash-circle.png', color: '#8dc351', name: 'Bitcoin Cash' },
    NEAR: { logo: 'https://assets.coingecko.com/coins/images/10365/small/near.jpg', color: '#00c08b', name: 'NEAR Protocol' },
    APT: { logo: 'https://assets.coingecko.com/coins/images/26455/small/aptos_round.png', color: '#4cd080', name: 'Aptos' },
    FIL: { logo: 'https://assets.coingecko.com/coins/images/12817/small/filecoin.png', color: '#0090ff', name: 'Filecoin' },
    ARB: { logo: 'https://assets.coingecko.com/coins/images/16547/small/photo_2023-03-29_21.47.00.jpeg', color: '#28a0f0', name: 'Arbitrum' },
    OP: { logo: 'https://assets.coingecko.com/coins/images/25244/small/Optimism.png', color: '#ff0420', name: 'Optimism' },
    VET: { logo: 'https://assets.coingecko.com/coins/images/1167/small/VeChain-Logo-768x725.png', color: '#15bdff', name: 'VeChain' },
    ALGO: { logo: 'https://assets.coingecko.com/coins/images/4380/small/download.png', color: '#000000', name: 'Algorand' },
    AAVE: { logo: 'https://assets.coingecko.com/coins/images/12645/small/AAVE.png', color: '#b6509e', name: 'Aave' },
    FTM: { logo: 'https://assets.coingecko.com/coins/images/4001/small/Fantom_round.png', color: '#1969ff', name: 'Fantom' },
    SAND: { logo: 'https://assets.coingecko.com/coins/images/12129/small/sandbox_logo.jpg', color: '#00adef', name: 'The Sandbox' },
    MANA: { logo: 'https://assets.coingecko.com/coins/images/878/small/decentraland-mana.png', color: '#ff2d55', name: 'Decentraland' },
    AXS: { logo: 'https://assets.coingecko.com/coins/images/13029/small/axie_infinity_logo.png', color: '#0055d5', name: 'Axie Infinity' },
    THETA: { logo: 'https://assets.coingecko.com/coins/images/2538/small/theta-token-logo.png', color: '#2ab8e6', name: 'Theta Network' },
    EGLD: { logo: 'https://assets.coingecko.com/coins/images/12335/small/multiversx.png', color: '#23f7dd', name: 'MultiversX' },
    XTZ: { logo: 'https://assets.coingecko.com/coins/images/976/small/Tezos-logo.png', color: '#2c7df7', name: 'Tezos' },
    EOS: { logo: 'https://assets.coingecko.com/coins/images/738/small/eos-eos-logo.png', color: '#000000', name: 'EOS' },
    FLOW: { logo: 'https://assets.coingecko.com/coins/images/13446/small/5f6294c0c7a8cda55cb1c936_Flow_Wordmark.png', color: '#00ef8b', name: 'Flow' },
    CHZ: { logo: 'https://assets.coingecko.com/coins/images/8834/small/CHZ_Token_updated.png', color: '#cd0124', name: 'Chiliz' },
    GALA: { logo: 'https://assets.coingecko.com/coins/images/12493/small/GALA-COINGECKO.png', color: '#000000', name: 'Gala' },
    CRV: { logo: 'https://assets.coingecko.com/coins/images/12124/small/Curve.png', color: '#ff2d2d', name: 'Curve DAO' },
    LDO: { logo: 'https://assets.coingecko.com/coins/images/13573/small/Lido_DAO.png', color: '#00a3ff', name: 'Lido DAO' },
    IMX: { logo: 'https://assets.coingecko.com/coins/images/17233/small/immutableX-symbol-BLK-RGB.png', color: '#17b5cb', name: 'Immutable' },
    RENDER: { logo: 'https://assets.coingecko.com/coins/images/11636/small/rndr.png', color: '#000000', name: 'Render' },
    INJ: { logo: 'https://assets.coingecko.com/coins/images/12882/small/Secondary_Symbol.png', color: '#00f2fe', name: 'Injective' },
    SUI: { logo: 'https://assets.coingecko.com/coins/images/26375/small/sui_asset.jpeg', color: '#4da2ff', name: 'Sui' },
    SEI: { logo: 'https://assets.coingecko.com/coins/images/28205/small/Sei_Logo_-_Transparent.png', color: '#9c1c1c', name: 'Sei' },
    TIA: { logo: 'https://assets.coingecko.com/coins/images/31967/small/tia.jpg', color: '#7b2bf9', name: 'Celestia' },
    PEPE: { logo: 'https://assets.coingecko.com/coins/images/29850/small/pepe-token.jpeg', color: '#479f53', name: 'Pepe' },
    WIF: { logo: 'https://assets.coingecko.com/coins/images/33566/small/dogwifhat.jpg', color: '#c4a574', name: 'dogwifhat' },
    BONK: { logo: 'https://assets.coingecko.com/coins/images/28600/small/bonk.jpg', color: '#f9a825', name: 'Bonk' },
    FLOKI: { logo: 'https://assets.coingecko.com/coins/images/16746/small/PNG_image.png', color: '#f5a623', name: 'Floki' },
    FET: { logo: 'https://assets.coingecko.com/coins/images/5681/small/Fetch.jpg', color: '#1c1c1c', name: 'Fetch.ai' },
    RNDR: { logo: 'https://assets.coingecko.com/coins/images/11636/small/rndr.png', color: '#000000', name: 'Render' },
    GRT: { logo: 'https://assets.coingecko.com/coins/images/13397/small/Graph_Token.png', color: '#6747ed', name: 'The Graph' },
    STX: { logo: 'https://assets.coingecko.com/coins/images/2069/small/Stacks_logo_full.png', color: '#5546ff', name: 'Stacks' },
    MKR: { logo: 'https://assets.coingecko.com/coins/images/1364/small/Mark_Maker.png', color: '#1aab9b', name: 'Maker' },
    RUNE: { logo: 'https://assets.coingecko.com/coins/images/6595/small/Rune200x200.png', color: '#33ff99', name: 'THORChain' },
    WLD: { logo: 'https://assets.coingecko.com/coins/images/31069/small/worldcoin.jpeg', color: '#000000', name: 'Worldcoin' },
    TAO: { logo: 'https://assets.coingecko.com/coins/images/28452/small/ARUsPeNQ_400x400.jpeg', color: '#000000', name: 'Bittensor' },
    JUP: { logo: 'https://assets.coingecko.com/coins/images/34188/small/jup.png', color: '#18e299', name: 'Jupiter' },
    STRK: { logo: 'https://assets.coingecko.com/coins/images/26433/small/starknet.png', color: '#ec796b', name: 'Starknet' },
    NOT: { logo: 'https://assets.coingecko.com/coins/images/36934/small/notcoin_logo.jpg', color: '#000000', name: 'Notcoin' },
    TON: { logo: 'https://assets.coingecko.com/coins/images/17980/small/ton_symbol.png', color: '#0098ea', name: 'Toncoin' },
    JASMY: { logo: 'https://assets.coingecko.com/coins/images/13876/small/JASMY200x200.jpg', color: '#ff7b00', name: 'JasmyCoin' },
    HBAR: { logo: 'https://assets.coingecko.com/coins/images/3688/small/hbar.png', color: '#000000', name: 'Hedera' },
    ICP: { logo: 'https://assets.coingecko.com/coins/images/14495/small/Internet_Computer_logo.png', color: '#29abe2', name: 'Internet Computer' },
    KAS: { logo: 'https://assets.coingecko.com/coins/images/25751/small/kaspa-icon-exchanges.png', color: '#70c7ba', name: 'Kaspa' },
    ENS: { logo: 'https://assets.coingecko.com/coins/images/19785/small/acatxTm8_400x400.jpg', color: '#5298ff', name: 'Ethereum Name Service' },
    PYTH: { logo: 'https://assets.coingecko.com/coins/images/31924/small/pyth.png', color: '#6633cc', name: 'Pyth Network' },
    ORDI: { logo: 'https://assets.coingecko.com/coins/images/30162/small/ordi.png', color: '#000000', name: 'ORDI' },
    BLUR: { logo: 'https://assets.coingecko.com/coins/images/28453/small/blur.png', color: '#ff6b00', name: 'Blur' },
    MASK: { logo: 'https://assets.coingecko.com/coins/images/14051/small/Mask_Network.jpg', color: '#1c68f3', name: 'Mask Network' },
    APE: { logo: 'https://assets.coingecko.com/coins/images/24383/small/apecoin.jpg', color: '#0038ff', name: 'ApeCoin' },
    CAKE: { logo: 'https://assets.coingecko.com/coins/images/12632/small/pancakeswap-cake-logo_%281%29.png', color: '#d1884f', name: 'PancakeSwap' },
    SNX: { logo: 'https://assets.coingecko.com/coins/images/3406/small/SNX.png', color: '#00d1ff', name: 'Synthetix' },
    COMP: { logo: 'https://assets.coingecko.com/coins/images/10775/small/COMP.png', color: '#00d395', name: 'Compound' },
    CRO: { logo: 'https://assets.coingecko.com/coins/images/7310/small/cro_token_logo.png', color: '#002d74', name: 'Cronos' },
    QNT: { logo: 'https://assets.coingecko.com/coins/images/3370/small/5ZOu7brX_400x400.jpg', color: '#000000', name: 'Quant' },
    KAVA: { logo: 'https://assets.coingecko.com/coins/images/9761/small/kava.png', color: '#ff433e', name: 'Kava' },
    ZEC: { logo: 'https://assets.coingecko.com/coins/images/486/small/circle-zcash-color.png', color: '#f4b728', name: 'Zcash' },
    MINA: { logo: 'https://assets.coingecko.com/coins/images/15628/small/JM4_vQ34_400x400.png', color: '#e39100', name: 'Mina Protocol' },
    NEO: { logo: 'https://assets.coingecko.com/coins/images/480/small/NEO_512_512.png', color: '#00e599', name: 'NEO' },
    XMR: { logo: 'https://assets.coingecko.com/coins/images/69/small/monero_logo.png', color: '#ff6600', name: 'Monero' },
    IOTA: { logo: 'https://assets.coingecko.com/coins/images/692/small/IOTA_Swirl.png', color: '#131f37', name: 'IOTA' },
    ZIL: { logo: 'https://assets.coingecko.com/coins/images/2687/small/Zilliqa-logo.png', color: '#49c1bf', name: 'Zilliqa' },
    DASH: { logo: 'https://assets.coingecko.com/coins/images/19/small/dash-logo.png', color: '#008ce7', name: 'Dash' },
    '1INCH': { logo: 'https://assets.coingecko.com/coins/images/13469/small/1inch-token.png', color: '#94a6c3', name: '1inch' },
    SUSHI: { logo: 'https://assets.coingecko.com/coins/images/12271/small/512x512_Logo_no_chop.png', color: '#fa52a0', name: 'SushiSwap' },
    YFI: { logo: 'https://assets.coingecko.com/coins/images/11849/small/yearn.jpg', color: '#006ae3', name: 'yearn.finance' },
    BAT: { logo: 'https://assets.coingecko.com/coins/images/677/small/basic-attention-token.png', color: '#ff4724', name: 'Basic Attention Token' },
    PEOPLE: { logo: 'https://assets.coingecko.com/coins/images/21401/small/dao.png', color: '#ffcc00', name: 'ConstitutionDAO' },
    LUNC: { logo: 'https://assets.coingecko.com/coins/images/8284/small/01_LusqQtw.png', color: '#ffe600', name: 'Terra Classic' },
    GMT: { logo: 'https://assets.coingecko.com/coins/images/23597/small/gmt.png', color: '#e8d655', name: 'STEPN' },
    CFX: { logo: 'https://assets.coingecko.com/coins/images/13079/small/3vuYMbjN.png', color: '#1d1d1d', name: 'Conflux' },
    DYDX: { logo: 'https://assets.coingecko.com/coins/images/17500/small/hjnIm9bV.jpg', color: '#6966ff', name: 'dYdX' },
    OCEAN: { logo: 'https://assets.coingecko.com/coins/images/3687/small/ocean-protocol-logo.jpg', color: '#000000', name: 'Ocean Protocol' },
    SSV: { logo: 'https://assets.coingecko.com/coins/images/19155/small/ssv.png', color: '#0f4bf8', name: 'ssv.network' },
    RPL: { logo: 'https://assets.coingecko.com/coins/images/2090/small/rocket_pool_%28RPL%29.png', color: '#ff7b47', name: 'Rocket Pool' },
    ONDO: { logo: 'https://assets.coingecko.com/coins/images/26580/small/ONDO.png', color: '#1b3b5f', name: 'Ondo' },
    ENA: { logo: 'https://assets.coingecko.com/coins/images/36530/small/ethena.png', color: '#000000', name: 'Ethena' },
    W: { logo: 'https://assets.coingecko.com/coins/images/35087/small/womrhole_logo_full_color_rgb_2000px_72ppi_fb766ac85a.png', color: '#ffffff', name: 'Wormhole' },
    PENDLE: { logo: 'https://assets.coingecko.com/coins/images/15069/small/Pendle_Logo_Normal-03.png', color: '#3058de', name: 'Pendle' },
    FDUSD: { logo: 'https://assets.coingecko.com/coins/images/31079/small/firstdigitalusd.jpg', color: '#0c7d50', name: 'First Digital USD' },
};

// NASDAQ Stock data with logos from financial modeling prep
const stockData: Record<string, { logo: string; color: string; name: string }> = {
    AAPL: { logo: 'https://financialmodelingprep.com/image-stock/AAPL.png', color: '#555555', name: 'Apple Inc.' },
    MSFT: { logo: 'https://financialmodelingprep.com/image-stock/MSFT.png', color: '#00a4ef', name: 'Microsoft Corporation' },
    GOOGL: { logo: 'https://financialmodelingprep.com/image-stock/GOOGL.png', color: '#4285f4', name: 'Alphabet Inc.' },
    AMZN: { logo: 'https://financialmodelingprep.com/image-stock/AMZN.png', color: '#ff9900', name: 'Amazon.com Inc.' },
    NVDA: { logo: 'https://financialmodelingprep.com/image-stock/NVDA.png', color: '#76b900', name: 'NVIDIA Corporation' },
    META: { logo: 'https://financialmodelingprep.com/image-stock/META.png', color: '#0668e1', name: 'Meta Platforms Inc.' },
    TSLA: { logo: 'https://financialmodelingprep.com/image-stock/TSLA.png', color: '#cc0000', name: 'Tesla Inc.' },
    AVGO: { logo: 'https://financialmodelingprep.com/image-stock/AVGO.png', color: '#cc092f', name: 'Broadcom Inc.' },
    COST: { logo: 'https://financialmodelingprep.com/image-stock/COST.png', color: '#e31837', name: 'Costco Wholesale' },
    NFLX: { logo: 'https://financialmodelingprep.com/image-stock/NFLX.png', color: '#e50914', name: 'Netflix Inc.' },
    AMD: { logo: 'https://financialmodelingprep.com/image-stock/AMD.png', color: '#ed1c24', name: 'Advanced Micro Devices' },
    ADBE: { logo: 'https://financialmodelingprep.com/image-stock/ADBE.png', color: '#ff0000', name: 'Adobe Inc.' },
    PEP: { logo: 'https://financialmodelingprep.com/image-stock/PEP.png', color: '#004b93', name: 'PepsiCo Inc.' },
    CSCO: { logo: 'https://financialmodelingprep.com/image-stock/CSCO.png', color: '#1ba0d7', name: 'Cisco Systems' },
    INTC: { logo: 'https://financialmodelingprep.com/image-stock/INTC.png', color: '#0071c5', name: 'Intel Corporation' },
    CMCSA: { logo: 'https://financialmodelingprep.com/image-stock/CMCSA.png', color: '#000000', name: 'Comcast Corporation' },
    TMUS: { logo: 'https://financialmodelingprep.com/image-stock/TMUS.png', color: '#e20074', name: 'T-Mobile US' },
    TXN: { logo: 'https://financialmodelingprep.com/image-stock/TXN.png', color: '#c4122f', name: 'Texas Instruments' },
    QCOM: { logo: 'https://financialmodelingprep.com/image-stock/QCOM.png', color: '#3253dc', name: 'Qualcomm Inc.' },
    INTU: { logo: 'https://financialmodelingprep.com/image-stock/INTU.png', color: '#365ebf', name: 'Intuit Inc.' },
    AMGN: { logo: 'https://financialmodelingprep.com/image-stock/AMGN.png', color: '#0063be', name: 'Amgen Inc.' },
    ISRG: { logo: 'https://financialmodelingprep.com/image-stock/ISRG.png', color: '#00539b', name: 'Intuitive Surgical' },
    HON: { logo: 'https://financialmodelingprep.com/image-stock/HON.png', color: '#d32f2f', name: 'Honeywell International' },
    AMAT: { logo: 'https://financialmodelingprep.com/image-stock/AMAT.png', color: '#00539b', name: 'Applied Materials' },
    BKNG: { logo: 'https://financialmodelingprep.com/image-stock/BKNG.png', color: '#003580', name: 'Booking Holdings' },
    SBUX: { logo: 'https://financialmodelingprep.com/image-stock/SBUX.png', color: '#00704a', name: 'Starbucks Corporation' },
    GILD: { logo: 'https://financialmodelingprep.com/image-stock/GILD.png', color: '#0c2340', name: 'Gilead Sciences' },
    ADP: { logo: 'https://financialmodelingprep.com/image-stock/ADP.png', color: '#d0021b', name: 'Automatic Data Processing' },
    VRTX: { logo: 'https://financialmodelingprep.com/image-stock/VRTX.png', color: '#000099', name: 'Vertex Pharmaceuticals' },
    PYPL: { logo: 'https://financialmodelingprep.com/image-stock/PYPL.png', color: '#003087', name: 'PayPal Holdings' },
};

// Get logo URL for a coin - uses mapping or generates fallback
const getCoinLogo = (symbol: string): string => {
    if (coinData[symbol]?.logo) {
        return coinData[symbol].logo;
    }
    // Fallback to CryptoLogos API
    return `https://cryptologos.cc/logos/${symbol.toLowerCase()}-${symbol.toLowerCase()}-logo.png?v=035`;
};

// Get logo URL for a stock - uses mapping or generates fallback with company initials
const getStockLogo = (symbol: string): string => {
    if (stockData[symbol]?.logo) {
        return stockData[symbol].logo;
    }
    // Fallback to ui-avatars with purple background
    return `https://ui-avatars.com/api/?name=${symbol}&background=4f46e5&color=fff&size=64&bold=true`;
};

// Get the appropriate logo for any asset type
const getAssetLogo = (symbol: string, providedLogo?: string, marketType: 'crypto' | 'nasdaq' = 'crypto'): string => {
    // First priority: use the logo provided by the API if it exists
    if (providedLogo) {
        return providedLogo;
    }
    // Second priority: use local mappings based on market type
    if (marketType === 'nasdaq') {
        return getStockLogo(symbol);
    }
    return getCoinLogo(symbol);
};

// Get asset name
const getAssetName = (symbol: string, providedName?: string, marketType: 'crypto' | 'nasdaq' = 'crypto'): string => {
    if (providedName) {
        return providedName;
    }
    if (marketType === 'nasdaq' && stockData[symbol]?.name) {
        return stockData[symbol].name;
    }
    return coinData[symbol]?.name || symbol;
};

// Get coin display name
const getCoinName = (symbol: string): string => {
    return coinData[symbol]?.name || symbol;
};

// Generate mock sparkline data
const generateSparkline = (baseChange: number): number[] => {
    const points = 7;
    const data: number[] = [];
    let value = 100;
    for (let i = 0; i < points; i++) {
        const change = (Math.random() - 0.5) * 10 + (baseChange / points);
        value = value + change;
        data.push(Math.max(0, value));
    }
    return data;
};

// Sparkline mini chart component
function SparklineChart({ data, positive }: { data: number[]; positive: boolean }) {
    const min = Math.min(...data);
    const max = Math.max(...data);
    const range = max - min || 1;
    const height = 32;
    const width = 100;
    const stepX = width / (data.length - 1);

    const points = data.map((value, index) => {
        const x = index * stepX;
        const y = height - ((value - min) / range) * height;
        return `${x},${y}`;
    }).join(' ');

    return (
        <svg width={width} height={height} className="overflow-visible">
            <polyline
                points={points}
                fill="none"
                stroke={positive ? '#22c55e' : '#ef4444'}
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
            />
        </svg>
    );
}

export default function OverviewPage({ marketType = 'crypto' }: { marketType?: 'crypto' | 'nasdaq' }) {
    const [fearGreedData, setFearGreedData] = useState<FearGreedData | null>(null);
    const [marketData, setMarketData] = useState<MarketOverview | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

    const fetchData = async () => {
        setIsLoading(true);
        try {
            if (marketType === 'nasdaq') {
                // Fetch NASDAQ data (includes Fear & Greed)
                const response = await fetch('http://localhost:8000/api/nasdaq-overview');
                const nasdaqData = await response.json();

                // Set market data
                setMarketData(nasdaqData);

                // Set Fear & Greed from NASDAQ response
                if (nasdaqData.fear_greed) {
                    setFearGreedData({
                        value: nasdaqData.fear_greed.value,
                        classification: nasdaqData.fear_greed.classification,
                        timestamp: nasdaqData.fear_greed.timestamp,
                        history: []
                    });
                }
            } else {
                // Fetch Crypto data
                const [fgData, mktData] = await Promise.all([
                    fetchFearGreedIndex(),
                    fetchMarketOverview()
                ]);
                setFearGreedData(fgData);
                setMarketData(mktData);
            }
            setLastUpdate(new Date());
        } catch (error) {
            console.error('Failed to fetch overview data:', error);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 120000);
        return () => clearInterval(interval);
    }, [marketType]);

    // Derived data for trending, gainers, losers
    const { topGainers, topLosers } = useMemo(() => {
        if (!marketData?.coins) return { topGainers: [], topLosers: [] };
        const sorted = [...marketData.coins].sort((a, b) => b.change_24h - a.change_24h);
        return {
            topGainers: sorted.slice(0, 3), // Top 3 best performers
            topLosers: sorted.slice(-3).reverse() // Bottom 3 worst performers
        };
    }, [marketData]);

    const formatPrice = (price: number) => {
        if (price >= 1000) {
            return `$${price.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
        }
        return `$${price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    };

    const formatLargeNumber = (num: number) => {
        if (num >= 1e12) return `$${(num / 1e12).toFixed(2)}T`;
        if (num >= 1e9) return `$${(num / 1e9).toFixed(2)}B`;
        if (num >= 1e6) return `$${(num / 1e6).toFixed(2)}M`;
        return `$${num.toLocaleString()}`;
    };

    const formatVolume = (num: number) => {
        if (num >= 1e12) return `$${(num / 1e12).toFixed(2)}T`;
        if (num >= 1e9) return `$${(num / 1e9).toFixed(1)}B`;
        if (num >= 1e6) return `$${(num / 1e6).toFixed(1)}M`;
        return `$${num.toLocaleString()}`;
    };

    const getFearGreedColor = (value: number) => {
        if (value <= 25) return '#ef4444';
        if (value <= 45) return '#f97316';
        if (value <= 55) return '#eab308';
        if (value <= 75) return '#84cc16';
        return '#22c55e';
    };

    return (
        <div className="h-full overflow-y-auto bg-oracle-darker">
            {/* ===== TOP MARKET STATS BAR ===== */}
            <div className="sticky top-0 z-10 bg-oracle-dark/95 backdrop-blur-md border-b border-oracle-border">
                <div className="max-w-[1800px] mx-auto px-4 py-3">
                    <div className="flex items-center justify-between">
                        {/* Left Stats */}
                        <div className="flex items-center gap-6 text-sm">
                            {/* Total Market Cap */}
                            <div className="flex items-center gap-2">
                                <span className="text-gray-400">Piyasa Değeri:</span>
                                <span className="font-semibold text-white">
                                    {marketData ? formatLargeNumber(marketData.total_market_cap) : '--'}
                                </span>
                                {marketData && (
                                    <span className={`text-xs px-1.5 py-0.5 rounded ${marketData.total_market_cap > 0 ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                                        +2.4%
                                    </span>
                                )}
                            </div>

                            <div className="w-px h-4 bg-oracle-border" />

                            {/* 24h Volume */}
                            <div className="flex items-center gap-2">
                                <span className="text-gray-400">24s Hacim:</span>
                                <span className="font-semibold text-white">
                                    {marketData ? formatLargeNumber(marketData.total_volume_24h) : '--'}
                                </span>
                            </div>

                            {/* BTC & ETH Dominance - Only show for crypto */}
                            {marketType === 'crypto' && (
                                <>
                                    <div className="w-px h-4 bg-oracle-border" />

                                    {/* BTC Dominance */}
                                    <div className="flex items-center gap-2">
                                        <span className="text-gray-400">BTC:</span>
                                        <div className="flex items-center gap-1.5">
                                            <span className="font-semibold text-orange-400">
                                                {marketData ? `${marketData.btc_dominance.toFixed(1)}%` : '--'}
                                            </span>
                                            <div className="w-16 h-1.5 bg-oracle-border rounded-full overflow-hidden">
                                                <div
                                                    className="h-full bg-gradient-to-r from-orange-500 to-orange-400 rounded-full transition-all"
                                                    style={{ width: marketData ? `${marketData.btc_dominance}%` : '0%' }}
                                                />
                                            </div>
                                        </div>
                                    </div>

                                    <div className="w-px h-4 bg-oracle-border" />

                                    {/* ETH Dominance */}
                                    <div className="flex items-center gap-2">
                                        <span className="text-gray-400">ETH:</span>
                                        <div className="flex items-center gap-1.5">
                                            <span className="font-semibold text-indigo-400">
                                                {marketData?.eth_dominance ? `${marketData.eth_dominance.toFixed(1)}%` : '--'}
                                            </span>
                                            <div className="w-16 h-1.5 bg-oracle-border rounded-full overflow-hidden">
                                                <div
                                                    className="h-full bg-gradient-to-r from-indigo-500 to-indigo-400 rounded-full transition-all"
                                                    style={{ width: marketData?.eth_dominance ? `${(marketData.eth_dominance / 20) * 100}%` : '0%' }}
                                                />
                                            </div>
                                        </div>
                                    </div>
                                </>
                            )}

                            <div className="w-px h-4 bg-oracle-border" />

                            {/* Fear & Greed Compact */}
                            <div className="flex items-center gap-2">
                                <Activity className="w-3.5 h-3.5 text-pink" />
                                <span className="text-gray-400">F&G:</span>
                                {fearGreedData && (
                                    <span
                                        className="font-bold"
                                        style={{ color: getFearGreedColor(fearGreedData.value) }}
                                    >
                                        {fearGreedData.value}
                                    </span>
                                )}
                            </div>
                        </div>

                        {/* Right - Refresh Button */}
                        <div className="flex items-center gap-3">
                            {lastUpdate && (
                                <span className="text-xs text-gray-500">
                                    Son: {lastUpdate.toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' })}
                                </span>
                            )}
                            <button
                                onClick={fetchData}
                                disabled={isLoading}
                                className="flex items-center gap-1.5 px-3 py-1.5 bg-oracle-card border border-oracle-border rounded-lg hover:border-violet transition-colors text-sm disabled:opacity-50"
                            >
                                <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
                                <span>Yenile</span>
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            <div className="max-w-[1800px] mx-auto px-4 py-6 space-y-6">
                {/* ===== TRENDING / GAINERS / LOSERS CARDS ===== */}
                <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
                    {/* Fear & Greed Card */}
                    <div className="lg:col-span-1 p-4 rounded-xl bg-gradient-to-br from-oracle-card to-pink/5 border border-oracle-border">
                        <div className="flex items-center gap-2 mb-3">
                            <Activity className="w-4 h-4 text-pink" />
                            <h3 className="font-semibold text-white text-sm">Fear & Greed Index</h3>
                        </div>
                        <FearGreedGauge data={fearGreedData} isLoading={isLoading} size="sm" />
                    </div>

                    {/* Trending */}
                    <div className="p-4 rounded-xl bg-gradient-to-br from-oracle-card to-violet/5 border border-oracle-border">
                        <div className="flex items-center justify-between mb-3">
                            <div className="flex items-center gap-2">
                                <Flame className="w-4 h-4 text-orange-400" />
                                <h3 className="font-semibold text-white text-sm">🔥 Trending</h3>
                            </div>
                            <ChevronRight className="w-4 h-4 text-gray-500" />
                        </div>
                        <div className="space-y-2">
                            {(isLoading ? [1, 2, 3] : marketData?.coins.slice(0, 3) || []).map((coin, i) => (
                                typeof coin === 'number' ? (
                                    <div key={i} className="flex items-center gap-2 animate-pulse">
                                        <div className="w-6 h-6 rounded-full bg-oracle-border" />
                                        <div className="flex-1 h-4 bg-oracle-border rounded" />
                                    </div>
                                ) : (
                                    <div key={coin.symbol} className="flex items-center justify-between">
                                        <div className="flex items-center gap-2">
                                            <span className="text-xs text-gray-500">{i + 1}</span>
                                            <img
                                                src={getAssetLogo(coin.symbol, coin.logo, marketType)}
                                                alt={coin.symbol}
                                                className="w-5 h-5 rounded-full object-cover bg-oracle-border"
                                                onError={(e) => { e.currentTarget.src = `https://ui-avatars.com/api/?name=${coin.symbol}&background=6b21a8&color=fff&size=40&bold=true`; }}
                                            />
                                            <span className="text-sm text-white">{coin.symbol}</span>
                                        </div>
                                        <span className={`text-xs font-medium ${coin.change_24h >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                            {coin.change_24h >= 0 ? '+' : ''}{coin.change_24h.toFixed(1)}%
                                        </span>
                                    </div>
                                )
                            ))}
                        </div>
                    </div>

                    {/* Top Gainers */}
                    <div className="p-4 rounded-xl bg-gradient-to-br from-oracle-card to-green-500/5 border border-oracle-border">
                        <div className="flex items-center justify-between mb-3">
                            <div className="flex items-center gap-2">
                                <TrendingUp className="w-4 h-4 text-green-400" />
                                <h3 className="font-semibold text-white text-sm">📈 Top Gainers</h3>
                            </div>
                            <ChevronRight className="w-4 h-4 text-gray-500" />
                        </div>
                        <div className="space-y-2">
                            {(isLoading ? [1, 2, 3] : topGainers).map((coin, i) => (
                                typeof coin === 'number' ? (
                                    <div key={i} className="flex items-center gap-2 animate-pulse">
                                        <div className="w-6 h-6 rounded-full bg-oracle-border" />
                                        <div className="flex-1 h-4 bg-oracle-border rounded" />
                                    </div>
                                ) : (
                                    <div key={coin.symbol} className="flex items-center justify-between">
                                        <div className="flex items-center gap-2">
                                            <img
                                                src={getAssetLogo(coin.symbol, coin.logo, marketType)}
                                                alt={coin.symbol}
                                                className="w-5 h-5 rounded-full object-cover bg-oracle-border"
                                                onError={(e) => { e.currentTarget.src = `https://ui-avatars.com/api/?name=${coin.symbol}&background=22c55e&color=fff&size=40&bold=true`; }}
                                            />
                                            <span className="text-sm text-white">{coin.symbol}</span>
                                        </div>
                                        <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-green-500/20 text-green-400">
                                            {coin.change_24h >= 0 ? '+' : ''}{coin.change_24h.toFixed(1)}%
                                        </span>
                                    </div>
                                )
                            ))}
                        </div>
                    </div>

                    {/* Top Losers */}
                    <div className="p-4 rounded-xl bg-gradient-to-br from-oracle-card to-red-500/5 border border-oracle-border">
                        <div className="flex items-center justify-between mb-3">
                            <div className="flex items-center gap-2">
                                <TrendingDown className="w-4 h-4 text-red-400" />
                                <h3 className="font-semibold text-white text-sm">📉 Top Losers</h3>
                            </div>
                            <ChevronRight className="w-4 h-4 text-gray-500" />
                        </div>
                        <div className="space-y-2">
                            {(isLoading ? [1, 2, 3] : topLosers).map((coin, i) => (
                                typeof coin === 'number' ? (
                                    <div key={i} className="flex items-center gap-2 animate-pulse">
                                        <div className="w-6 h-6 rounded-full bg-oracle-border" />
                                        <div className="flex-1 h-4 bg-oracle-border rounded" />
                                    </div>
                                ) : (
                                    <div key={coin.symbol} className="flex items-center justify-between">
                                        <div className="flex items-center gap-2">
                                            <img
                                                src={getAssetLogo(coin.symbol, coin.logo, marketType)}
                                                alt={coin.symbol}
                                                className="w-5 h-5 rounded-full object-cover bg-oracle-border"
                                                onError={(e) => { e.currentTarget.src = `https://ui-avatars.com/api/?name=${coin.symbol}&background=ef4444&color=fff&size=40&bold=true`; }}
                                            />
                                            <span className="text-sm text-white">{coin.symbol}</span>
                                        </div>
                                        <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-red-500/20 text-red-400">
                                            {coin.change_24h.toFixed(1)}%
                                        </span>
                                    </div>
                                )
                            ))}
                        </div>
                    </div>
                </div>

                {/* ===== CRYPTOCURRENCY TABLE ===== */}
                <div className="rounded-xl bg-oracle-card border border-oracle-border overflow-hidden">
                    <div className="px-4 py-3 border-b border-oracle-border flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <Coins className="w-5 h-5 text-cyan" />
                            <h2 className="font-semibold text-white">
                                {marketType === 'nasdaq' ? 'Hisse Senedi Listesi' : 'Kripto Para Listesi'}
                            </h2>
                        </div>
                        <div className="flex items-center gap-2 text-xs text-gray-500">
                            <Globe className="w-3.5 h-3.5" />
                            <span>{marketData?.active_cryptocurrencies?.toLocaleString() || '--'} {marketType === 'nasdaq' ? 'aktif hisse' : 'aktif kripto'}</span>
                        </div>
                    </div>

                    {/* Table Header */}
                    <div className="grid grid-cols-[40px_1fr_120px_100px_100px_130px_130px_110px] gap-2 px-4 py-2 text-xs text-gray-400 border-b border-oracle-border bg-oracle-dark/50">
                        <div className="text-center">#</div>
                        <div>İsim</div>
                        <div className="text-right">Fiyat</div>
                        <div className="text-right">24s %</div>
                        <div className="text-right">7g %</div>
                        <div className="text-right">Piyasa Değeri</div>
                        <div className="text-right">Hacim (24s)</div>
                        <div className="text-right">Son 7 Gün</div>
                    </div>

                    {/* Table Body */}
                    <div className="divide-y divide-oracle-border/50">
                        {isLoading ? (
                            // Loading skeleton
                            [...Array(8)].map((_, i) => (
                                <div key={i} className="grid grid-cols-[40px_1fr_120px_100px_100px_130px_130px_110px] gap-2 px-4 py-3 animate-pulse">
                                    <div className="flex justify-center"><div className="w-5 h-5 bg-oracle-border rounded" /></div>
                                    <div className="flex items-center gap-3">
                                        <div className="w-8 h-8 bg-oracle-border rounded-full" />
                                        <div className="space-y-1">
                                            <div className="w-20 h-4 bg-oracle-border rounded" />
                                            <div className="w-12 h-3 bg-oracle-border rounded" />
                                        </div>
                                    </div>
                                    <div className="w-16 h-5 bg-oracle-border rounded ml-auto" />
                                    <div className="w-14 h-5 bg-oracle-border rounded ml-auto" />
                                    <div className="w-14 h-5 bg-oracle-border rounded ml-auto" />
                                    <div className="w-20 h-5 bg-oracle-border rounded ml-auto" />
                                    <div className="w-20 h-5 bg-oracle-border rounded ml-auto" />
                                    <div className="w-24 h-8 bg-oracle-border rounded ml-auto" />
                                </div>
                            ))
                        ) : (
                            marketData?.coins.map((coin, index) => {
                                const sparklineData = generateSparkline(coin.change_24h);
                                const change7d = coin.change_24h * (0.5 + Math.random());

                                return (
                                    <div
                                        key={coin.symbol}
                                        className="grid grid-cols-[40px_1fr_120px_100px_100px_130px_130px_110px] gap-2 px-4 py-3 hover:bg-oracle-card-hover transition-colors group cursor-pointer"
                                    >
                                        {/* Rank */}
                                        <div className="flex items-center justify-center text-gray-500 text-sm">
                                            {index + 1}
                                        </div>

                                        {/* Name + Symbol */}
                                        <div className="flex items-center gap-3">
                                            <img
                                                src={getAssetLogo(coin.symbol, coin.logo, marketType)}
                                                alt={coin.symbol}
                                                className="w-8 h-8 rounded-full object-cover bg-oracle-border"
                                                onError={(e) => { e.currentTarget.src = `https://ui-avatars.com/api/?name=${coin.symbol}&background=4f46e5&color=fff&size=64&bold=true`; }}
                                            />
                                            <div>
                                                <p className="font-medium text-white group-hover:text-cyan transition-colors">
                                                    {getAssetName(coin.symbol, coin.name, marketType)}
                                                </p>
                                                <p className="text-xs text-gray-500">{coin.symbol}</p>
                                            </div>
                                        </div>

                                        {/* Price */}
                                        <div className="flex items-center justify-end font-medium text-white">
                                            {formatPrice(coin.price)}
                                        </div>

                                        {/* 24h Change */}
                                        <div className="flex items-center justify-end">
                                            <span className={`flex items-center gap-1 text-sm font-medium ${coin.change_24h >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                                {coin.change_24h >= 0 ? <ArrowUp className="w-3 h-3" /> : <ArrowDown className="w-3 h-3" />}
                                                {Math.abs(coin.change_24h).toFixed(2)}%
                                            </span>
                                        </div>

                                        {/* 7d Change */}
                                        <div className="flex items-center justify-end">
                                            <span className={`text-sm font-medium ${change7d >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                                {change7d >= 0 ? '+' : ''}{change7d.toFixed(2)}%
                                            </span>
                                        </div>

                                        {/* Market Cap */}
                                        <div className="flex items-center justify-end text-sm text-gray-300">
                                            {formatVolume(coin.market_cap)}
                                        </div>

                                        {/* Volume */}
                                        <div className="flex items-center justify-end text-sm text-gray-300">
                                            {formatVolume(coin.volume_24h)}
                                        </div>

                                        {/* Sparkline */}
                                        <div className="flex items-center justify-end">
                                            <SparklineChart data={sparklineData} positive={coin.change_24h >= 0} />
                                        </div>
                                    </div>
                                );
                            })
                        )}
                    </div>
                </div>

                {/* ===== BOTTOM STATS ===== */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {/* Quick Stats Cards */}
                    <div className="p-4 rounded-xl bg-gradient-to-br from-oracle-card to-violet/10 border border-oracle-border">
                        <div className="flex items-center gap-2 mb-2">
                            <Globe className="w-4 h-4 text-violet-400" />
                            <span className="text-xs text-gray-400">Toplam Piyasa Değeri</span>
                        </div>
                        <p className="text-xl font-bold text-white">
                            {marketData ? formatLargeNumber(marketData.total_market_cap) : '--'}
                        </p>
                    </div>

                    <div className="p-4 rounded-xl bg-gradient-to-br from-oracle-card to-cyan/10 border border-oracle-border">
                        <div className="flex items-center gap-2 mb-2">
                            <BarChart2 className="w-4 h-4 text-cyan" />
                            <span className="text-xs text-gray-400">24 Saatlik Hacim</span>
                        </div>
                        <p className="text-xl font-bold text-white">
                            {marketData ? formatLargeNumber(marketData.total_volume_24h) : '--'}
                        </p>
                    </div>

                    <div className="p-4 rounded-xl bg-gradient-to-br from-oracle-card to-orange-500/10 border border-oracle-border">
                        <div className="flex items-center gap-2 mb-2">
                            <Zap className="w-4 h-4 text-orange-400" />
                            <span className="text-xs text-gray-400">{marketType === 'nasdaq' ? 'Technology Ağırlığı' : 'BTC Dominance'}</span>
                        </div>
                        <p className="text-xl font-bold text-white">
                            {marketType === 'nasdaq' ? 'N/A' : (marketData ? `${marketData.btc_dominance.toFixed(1)}%` : '--')}
                        </p>
                    </div>

                    <div className="p-4 rounded-xl bg-gradient-to-br from-oracle-card to-green-500/10 border border-oracle-border">
                        <div className="flex items-center gap-2 mb-2">
                            <Coins className="w-4 h-4 text-green-400" />
                            <span className="text-xs text-gray-400">{marketType === 'nasdaq' ? 'Aktif Hisse' : 'Aktif Kripto Para'}</span>
                        </div>
                        <p className="text-xl font-bold text-white">
                            {marketData ? marketData.active_cryptocurrencies.toLocaleString() : '--'}
                        </p>
                    </div>
                </div>
            </div>
        </div >
    );
}

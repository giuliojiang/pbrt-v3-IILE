import plotly
import plotly.plotly as py
import plotly.graph_objs as go

# IILE render -----------------------------------------------------------------

xData = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024]

yRenderTime = [
    3, #1
    6, #2
    11, #4
    21, #8
    42, #16
    84, #32
    167, #64
    334, #128
    667, #256
    1342, #512
    2682 # 1024
]

yEntropy = [
    2392, #1
    2428, #2
    2364, #4
    2264, #8
    2020, #16
    1840, #32
    1696, #64
    1528, #128
    1368, #256
    1180, #512
    1032 # 1024
]

yPSNR = [
    181.06, #1
    187.33, #2
    192.22, #4
    196.64, #8
    203.17, #16
    208.55, #32
    213.68, #64
    220.36, #128
    227.86, #256
    236.03, #512
    243.66 # 1024
]

traceRenderTime = go.Scatter(
    x=xData,
    y=yRenderTime,
    name="Render time",
    yaxis="y"
)

traceEntropy = go.Scatter(
    x=xData,
    y=yEntropy,
    name="Entropy",
    yaxis="y2"
)

tracePSNR = go.Scatter(
    x=xData,
    y=yPSNR,
    name="PSNR",
    yaxis="y3"
)

data = [traceRenderTime, traceEntropy, tracePSNR]

title = "Path Mbed1"
xAxisLabel = "SPP"

layout = go.Layout(
    title=title,
    xaxis=dict(
        title=xAxisLabel,
        domain=[0.25, 0.7],
        type="log"
    ),
    yaxis=dict(
        title="Render time (seconds)",
        range=[0, 2700]
    ),
    yaxis2=dict(
        title="Entropy (kB)",
        overlaying="y",
        anchor="free",
        side="left",
        position=0.15,
        range=[0, 2500]
    ),
    yaxis3=dict(
        title="PSNR (dB)",
        overlaying="y",
        anchor="x",
        side="right",
        range=[170, 250]
    )
)

plotly.offline.plot(
    {
        "data": data,
        "layout": layout
    }
)
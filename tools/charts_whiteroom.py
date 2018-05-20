import plotly
import plotly.plotly as py
import plotly.graph_objs as go

# IILE render -----------------------------------------------------------------

xData = [0, 1, 2, 4, 8, 16, 32, 64, 128, 256, 512]

yRenderTime = [
    35, # 0
    45, #1
    44, #2
    48, #4
    56, #8
    75, #16
    113, #32
    202, #64
    401, #128
    772, #256
    1578, #512
]

yEntropy = [
    1048, # 0
    1232, #1
    1240, #2
    1180, #4
    1148, #8
    1128, #16
    1112, #32
    1096, #64
    1092, #128
    1080, #256
    1076, #512
]

yPSNR = [
    187, #0
    189, #1
    188, #2
    189, #4
    190, #8
    191, #16
    191, #32
    191, #64
    191.45, #128
    191.58, #256
    191.63, #512
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

title = "IILE White Room Daytime"
xAxisLabel = "Tasks"

layout = go.Layout(
    title=title,
    xaxis=dict(
        title=xAxisLabel,
        domain=[0.25, 0.7],
        type="log"
    ),
    yaxis=dict(
        title="Render time (seconds)",
        range=[0, 2500]
    ),
    yaxis2=dict(
        title="Entropy (kB)",
        overlaying="y",
        anchor="free",
        side="left",
        position=0.15,
        range=[0, 2000]
    ),
    yaxis3=dict(
        title="PSNR (dB)",
        overlaying="y",
        anchor="x",
        side="right",
        range=[170, 240]
    )
)

plotly.offline.plot(
    {
        "data": data,
        "layout": layout
    }
)
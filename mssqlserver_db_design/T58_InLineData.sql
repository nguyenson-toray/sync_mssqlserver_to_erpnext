USE [Production]
GO

/****** Object:  Table [dbo].[T58_InLineData]    Script Date: 2025-07-22 19:54:46 ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

CREATE TABLE [dbo].[T58_InLineData](
	[ID] [int] IDENTITY(1,1) NOT NULL,
	[X01] [int] NULL,
	[X02] [datetime] NULL,
	[X03] [int] NULL,
	[X04] [nvarchar](255) NULL,
	[X05] [int] NULL,
	[X06] [int] NULL,
	[X08] [int] NULL,
	[A01] [int] NULL,
	[A02] [int] NULL,
	[A03] [int] NULL,
	[B01] [int] NULL,
	[B02] [int] NULL,
	[B03] [int] NULL,
	[C01] [int] NULL,
	[C02] [int] NULL,
	[D01] [int] NULL,
	[D02] [int] NULL,
	[D03] [int] NULL,
	[D04] [int] NULL,
	[E01] [int] NULL,
	[E02] [int] NULL,
	[E03] [int] NULL,
	[E04] [int] NULL,
	[E05] [int] NULL,
	[E06] [int] NULL,
	[E07] [int] NULL,
	[F01] [int] NULL,
	[F02] [int] NULL,
	[F03] [int] NULL,
	[F04] [int] NULL,
	[F05] [int] NULL,
	[F06] [int] NULL,
	[F07] [int] NULL,
	[F08] [int] NULL,
	[F09] [int] NULL,
	[G01] [int] NULL,
	[G02] [int] NULL,
	[G03] [int] NULL,
	[H] [int] NULL,
	[X07] [nvarchar](255) NULL,
 CONSTRAINT [PK_T58_InLineData] PRIMARY KEY CLUSTERED 
(
	[ID] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO


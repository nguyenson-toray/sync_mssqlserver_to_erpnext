USE [Production]
GO

/****** Object:  Table [dbo].[T50_InspectionData]    Script Date: 2025-07-19 09:19:02 ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

CREATE TABLE [dbo].[T50_InspectionData](
	[ID] [int] IDENTITY(1,1) NOT NULL,
	[2nd] [int] NULL,
	[X01] [int] NULL,
	[X02] [datetime] NULL,
	[X03] [int] NULL,
	[X04] [nvarchar](255) NULL,
	[X05] [nvarchar](255) NULL,
	[X06] [int] NULL,
	[X07] [int] NULL,
	[X08] [int] NULL,
	[X09] [int] NULL,
	[X10] [int] NULL,
	[A01] [int] NULL,
	[A02] [int] NULL,
	[B01] [int] NULL,
	[B02] [int] NULL,
	[B03] [int] NULL,
	[C01] [int] NULL,
	[C02] [int] NULL,
	[D01] [int] NULL,
	[D02] [int] NULL,
	[D03] [int] NULL,
	[D04] [int] NULL,
	[D05] [int] NULL,
	[D06] [int] NULL,
	[D07] [int] NULL,
	[D08] [int] NULL,
	[E01] [int] NULL,
	[E02] [int] NULL,
	[E03] [int] NULL,
	[E04] [int] NULL,
	[E05] [int] NULL,
	[E06] [int] NULL,
	[E07] [int] NULL,
	[E08] [int] NULL,
	[E09] [int] NULL,
	[E10] [int] NULL,
	[E11] [int] NULL,
	[E12] [int] NULL,
	[E13] [int] NULL,
	[E14] [int] NULL,
	[E15] [int] NULL,
	[E16] [int] NULL,
	[E17] [int] NULL,
	[E18] [int] NULL,
	[E19] [int] NULL,
	[E20] [int] NULL,
	[E21] [int] NULL,
	[E22] [int] NULL,
	[E23] [int] NULL,
	[E24] [int] NULL,
	[F01] [int] NULL,
	[F02] [int] NULL,
	[F03] [int] NULL,
	[F04] [int] NULL,
	[F05] [int] NULL,
	[F06] [int] NULL,
	[F07] [int] NULL,
	[F08] [int] NULL,
	[F09] [int] NULL,
	[F10] [int] NULL,
	[F11] [int] NULL,
	[F12] [int] NULL,
	[F13] [int] NULL,
	[F14] [int] NULL,
	[F15] [int] NULL,
	[G01] [int] NULL,
	[G02] [int] NULL,
	[G03] [int] NULL,
	[G04] [int] NULL,
	[H] [int] NULL,
	[XC] [nvarchar](max) NULL,
 CONSTRAINT [PK_T50_InspectionData_1] PRIMARY KEY CLUSTERED 
(
	[ID] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO


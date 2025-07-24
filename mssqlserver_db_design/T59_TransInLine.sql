USE [Production]
GO

/****** Object:  Table [dbo].[T59_TransInLine]    Script Date: 2025-07-22 20:26:14 ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

CREATE TABLE [dbo].[T59_TransInLine](
	[ID] [int] IDENTITY(1,1) NOT NULL,
	[item] [int] NULL,
	[Process] [int] NULL,
	[MajorViet] [nvarchar](255) NULL,
	[MajorJpn] [nvarchar](255) NULL,
	[ProViet] [nvarchar](255) NULL,
	[ProJpn] [nvarchar](255) NULL,
 CONSTRAINT [PK_T59_TransInLine] PRIMARY KEY CLUSTERED 
(
	[ID] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO


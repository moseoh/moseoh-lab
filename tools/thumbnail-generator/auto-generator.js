import sharp from "sharp";
import fs from "fs/promises";
import path from "path";
import chalk from "chalk";

export class AutoThumbnailGenerator {
  constructor(configPath) {
    this.config = null;
    this.configPath = configPath;
  }

  async loadConfig() {
    try {
      const configData = await fs.readFile(this.configPath, "utf-8");
      this.config = JSON.parse(configData);
    } catch (error) {
      throw new Error(`${this.configPath} 파일을 읽을 수 없습니다`);
    }
  }

  async scanAssetsFolder() {
    try {
      const files = await fs.readdir(this.config.paths.assets);
      return files.filter((file) => {
        const ext = path.extname(file).toLowerCase();
        return (
          ext === ".svg" || ext === ".png" || ext === ".jpg" || ext === ".jpeg"
        );
      });
    } catch (error) {
      throw new Error(`assets 폴더를 읽을 수 없습니다: ${error.message}`);
    }
  }

  parseFileName(fileName) {
    const nameWithoutExt = path.parse(fileName).name;
    const parts = nameWithoutExt.split(this.config.fileConvention.separator);

    if (parts.length < 2) {
      throw new Error(
        `파일명 형식이 올바르지 않습니다: ${fileName}. 형식: {로고이름}-{배경색상} 또는 {로고이름}-{로고색상}-{배경색상}`,
      );
    }

    let logoName, logoColor, backgroundColor;

    if (parts.length === 2) {
      // {로고이름}-{배경색상} 형식
      logoName = parts[0];
      logoColor = null; // 로고 색상 변경 안함
      backgroundColor = parts[1];
    } else {
      // {로고이름}-{로고색상}-{배경색상} 형식 (3개 이상)
      logoName = parts.slice(0, -2).join(this.config.fileConvention.separator);
      logoColor = parts[parts.length - 2];
      backgroundColor = parts[parts.length - 1];
    }

    return {
      logoName,
      logoColor: logoColor ? this.normalizeColor(logoColor) : null,
      backgroundColor: this.normalizeColor(backgroundColor),
      originalFileName: fileName,
    };
  }

  normalizeColor(colorValue) {
    if (colorValue.startsWith("#")) {
      return colorValue;
    }

    if (colorValue.match(/^[0-9a-fA-F]{6}$/)) {
      return `#${colorValue}`;
    }

    if (colorValue.match(/^[0-9a-fA-F]{3}$/)) {
      return `#${colorValue}`;
    }

    const namedColors = {
      red: "#ff0000",
      green: "#00ff00",
      blue: "#0000ff",
      yellow: "#ffff00",
      purple: "#800080",
      orange: "#ffa500",
      pink: "#ffc0cb",
      brown: "#a52a2a",
      gray: "#808080",
      black: "#000000",
      white: "#ffffff",
    };

    return (
      namedColors[colorValue.toLowerCase()] ||
      this.config.thumbnail.defaultBackground
    );
  }

  calculateDimensions() {
    const rateParts = this.config.thumbnail.ratio.split(":");
    const width = this.config.thumbnail.width;
    const aspectRatio = parseInt(rateParts[0]) / parseInt(rateParts[1]);
    const height = Math.round(width / aspectRatio);

    return { width, height };
  }

  async processSvgColor(svgBuffer, logoColor) {
    try {
      let svgContent = svgBuffer.toString("utf-8");

      // 잘못된 네임스페이스 제거
      svgContent = svgContent.replace(/xmlns:x="ns_extend;"/g, "");
      svgContent = svgContent.replace(/xmlns:i="ns_ai;"/g, "");
      svgContent = svgContent.replace(/xmlns:graph="ns_graphs;"/g, "");
      svgContent = svgContent.replace(/<sfw[^>]*>[\s\S]*?<\/sfw>/g, "");
      svgContent = svgContent.replace(
        /<metadata[^>]*>[\s\S]*?<\/metadata>/g,
        "",
      );

      // SVG의 fill 속성을 로고 색상으로 변경
      svgContent = svgContent.replace(/fill="[^"]*"/g, `fill="${logoColor}"`);
      svgContent = svgContent.replace(/fill:[^;"]*/g, `fill:${logoColor}`);

      // CSS 스타일에서 fill 색상 변경
      svgContent = svgContent.replace(
        /\.st\d+\s*\{\s*fill:\s*[^;}]+\s*;\s*\}/g,
        `.st0{fill:${logoColor};}`,
      );

      // stroke 색상도 변경 (선택적)
      if (svgContent.includes("stroke=")) {
        svgContent = svgContent.replace(
          /stroke="[^"]*"/g,
          `stroke="${logoColor}"`,
        );
        svgContent = svgContent.replace(
          /stroke:[^;"]*/g,
          `stroke:${logoColor}`,
        );
      }

      return Buffer.from(svgContent, "utf-8");
    } catch (error) {
      throw new Error(`SVG 색상 처리 실패: ${error.message}`);
    }
  }

  async generateThumbnail(logoPath, logoColor, backgroundColor, outputPath) {
    try {
      const dimensions = this.calculateDimensions();

      let logoBuffer = await fs.readFile(logoPath);
      const fileExt = path.extname(logoPath).toLowerCase();

      // SVG인 경우 색상 변경 (logoColor가 있을 때만)
      if (fileExt === ".svg" && logoColor) {
        logoBuffer = await this.processSvgColor(logoBuffer, logoColor);
      }

      const logoMetadata = await sharp(logoBuffer).metadata();

      // config에서 설정한 비율로 최대 크기 계산
      const maxHeight = Math.round(
        dimensions.height * this.config.logo.heightRatio,
      );
      const maxWidth = Math.round(
        dimensions.width * this.config.logo.widthRatio,
      );

      let resizedLogo;
      // height 우선 적용, 그 다음 width 제한
      resizedLogo = await sharp(logoBuffer)
        .resize({
          height: maxHeight,
          width: maxWidth,
          fit: "inside",
          withoutEnlargement: false,
          kernel: sharp.kernel.lanczos3,
        })
        .toBuffer();

      const resizedLogoMetadata = await sharp(resizedLogo).metadata();

      const thumbnail = await sharp({
        create: {
          width: dimensions.width,
          height: dimensions.height,
          channels: 4,
          background: backgroundColor,
        },
      })
        .composite([
          {
            input: resizedLogo,
            left: Math.round(
              (dimensions.width - resizedLogoMetadata.width) / 2,
            ),
            top: Math.round(
              (dimensions.height - resizedLogoMetadata.height) / 2,
            ),
          },
        ])
        .png({
          quality: 100,
          compressionLevel: 0,
          progressive: false,
        })
        .toBuffer();

      await fs.mkdir(path.dirname(outputPath), { recursive: true });
      await fs.writeFile(outputPath, thumbnail);

      return {
        success: true,
        dimensions,
        logoSize: {
          width: resizedLogoMetadata.width,
          height: resizedLogoMetadata.height,
        },
      };
    } catch (error) {
      throw new Error(`썸네일 생성 실패: ${error.message}`);
    }
  }

  async copyToTarget(sourcePath, targetFileName) {
    try {
      await fs.access(this.config.paths.target);
      const targetPath = path.join(this.config.paths.target, targetFileName);
      await fs.copyFile(sourcePath, targetPath);
      return targetPath;
    } catch (error) {
      if (error.code === "ENOENT") {
        console.log(
          chalk.yellow(
            `⚠️  타겟 경로가 존재하지 않아 복사를 건너뜁니다: ${this.config.paths.target}`,
          ),
        );
        return null;
      }
      throw error;
    }
  }

  async generateAll() {
    try {
      await this.loadConfig();

      console.log(chalk.blue("🚀 자동 썸네일 생성을 시작합니다..."));
      console.log(
        chalk.gray(
          `설정: ${this.config.thumbnail.width}x${
            this.calculateDimensions().height
          } (${this.config.thumbnail.ratio})`,
        ),
      );

      const assetFiles = await this.scanAssetsFolder();

      if (assetFiles.length === 0) {
        console.log(
          chalk.yellow(
            `⚠️  ${this.config.paths.assets} 폴더에 이미지 파일이 없습니다.`,
          ),
        );
        return;
      }

      console.log(chalk.gray(`발견된 파일: ${assetFiles.length}개`));

      let successCount = 0;
      let errorCount = 0;

      for (const file of assetFiles) {
        try {
          const parsed = this.parseFileName(file);
          const logoPath = path.join(this.config.paths.assets, file);
          const outputFileName = `${parsed.logoName}.png`;
          const outputPath = path.join(
            this.config.paths.output,
            outputFileName,
          );

          // 파일이 이미 존재하는지 확인
          try {
            await fs.access(outputPath);
            console.log(
              chalk.yellow(`⏭️  스킵: ${outputFileName} (이미 존재)`),
            );
            successCount++;
            continue;
          } catch {
            // 파일이 없으면 생성 진행
          }

          const logoColorText = parsed.logoColor
            ? `로고: ${parsed.logoColor}, `
            : "";
          console.log(
            chalk.cyan(
              `📸 생성 중: ${parsed.logoName} (${logoColorText}배경: ${parsed.backgroundColor})`,
            ),
          );

          const result = await this.generateThumbnail(
            logoPath,
            parsed.logoColor,
            parsed.backgroundColor,
            outputPath,
          );

          const targetPath = await this.copyToTarget(
            outputPath,
            outputFileName,
          );

          console.log(chalk.green(`✅ 완료: ${outputFileName}`));
          if (targetPath) {
            console.log(chalk.gray(`   📁 복사됨: ${targetPath}`));
          }

          successCount++;
        } catch (error) {
          console.error(chalk.red(`❌ 실패: ${file} - ${error.message}`));
          errorCount++;
        }
      }

      console.log(chalk.blue("\n📊 결과:"));
      console.log(chalk.green(`✅ 성공: ${successCount}개`));
      if (errorCount > 0) {
        console.log(chalk.red(`❌ 실패: ${errorCount}개`));
      }
    } catch (error) {
      console.error(chalk.red("❌ 오류:"), error.message);
      process.exit(1);
    }
  }
}

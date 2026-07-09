import fs from 'node:fs/promises';
import path from 'node:path';
import process from 'node:process';

const IMAGE_URL_PATTERN = /_apis\/wit\/attachments\/([0-9a-fA-F-]{36})(?:\?fileName=([^"'&>\s]+))?/i;
const IMAGE_TAG_PATTERN = /<img[^>]*src=["']([^"']+)["'][^>]*>/gi;

function parseArguments(argv) {
  const options = {
    workItemFile: undefined,
    commentsFile: undefined,
    rawDir: undefined,
    preserveExistingStatus: true,
  };

  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];

    switch (argument) {
      case '--work-item-file':
        options.workItemFile = argv[index + 1];
        index += 1;
        break;
      case '--comments-file':
        options.commentsFile = argv[index + 1];
        index += 1;
        break;
      case '--raw-dir':
        options.rawDir = argv[index + 1];
        index += 1;
        break;
      case '--no-preserve-existing-status':
        options.preserveExistingStatus = false;
        break;
      default:
        throw new Error(`Unknown argument: ${argument}`);
    }
  }

  if (!options.workItemFile || !options.rawDir) {
    throw new Error('Usage: node scripts/azure/normalize-devops-story.mjs --work-item-file <path> --raw-dir <path> [--comments-file <path>]');
  }

  return options;
}

function decodeHtml(value) {
  return value
    .replaceAll('&nbsp;', ' ')
    .replaceAll('&amp;', '&')
    .replaceAll('&lt;', '<')
    .replaceAll('&gt;', '>')
    .replaceAll('&quot;', '"')
    .replaceAll('&#39;', "'")
    .replace(/&#(\d+);/g, (_, codePoint) => String.fromCodePoint(Number(codePoint)))
    .replace(/&#x([0-9a-f]+);/gi, (_, codePoint) => String.fromCodePoint(Number.parseInt(codePoint, 16)));
}

function sanitizeFileName(fileName) {
  if (!fileName) {
    return 'attachment.bin';
  }

  return fileName.replace(/[^A-Za-z0-9._-]/g, '_');
}

function slugifyLabel(label) {
  return label
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '')
    .replace(/_{2,}/g, '_');
}

function readAssignedToValue(value) {
  if (!value) {
    return '';
  }

  if (typeof value === 'string') {
    return value;
  }

  return value.displayName ?? value.uniqueName ?? '';
}

function buildAttachmentUrl(matchUrl, attachmentId, fileName) {
  if (matchUrl) {
    return matchUrl;
  }

  const suffix = fileName ? `?fileName=${encodeURIComponent(fileName)}` : '';
  return `https://dev.azure.com/danfoss/_apis/wit/attachments/${attachmentId}${suffix}`;
}

function createAttachmentCollector(previousManifest) {
  const attachments = new Map();

  function recordAttachment({ attachmentId, fileName, source, sourceType, url, suggestedLocalFileName }) {
    if (!attachmentId || attachments.has(attachmentId)) {
      return;
    }

    const previous = previousManifest.get(attachmentId);
    attachments.set(attachmentId, {
      attachmentId,
      fileName,
      source,
      sourceType,
      url,
      suggestedLocalFileName,
      attachmentAnalysis: previous?.attachmentAnalysis ?? previous?.['attachment analysis'] ?? '',
    });
  }

  function recordInlineAttachment(url, source, sourceType, filePrefix) {
    const match = url.match(IMAGE_URL_PATTERN);
    if (!match) {
      return undefined;
    }

    const attachmentId = match[1];
    const fileName = decodeURIComponent(match[2] ?? 'image.png');
    const suggestedLocalFileName = `${slugifyLabel(filePrefix)}_${attachmentId.slice(0, 8)}_${sanitizeFileName(fileName)}`;
    recordAttachment({
      attachmentId,
      fileName,
      source,
      sourceType,
      url: buildAttachmentUrl(url, attachmentId, fileName),
      suggestedLocalFileName,
    });

    return attachmentId;
  }

  function recordAttachedFile(entry) {
    if (!entry?.attachmentId) {
      return;
    }

    recordAttachment({
      attachmentId: entry.attachmentId,
      fileName: entry.name ?? entry.fileName ?? 'attachment.bin',
      source: entry.source ?? 'relation:AttachedFile',
      sourceType: 'attachedFile',
      url: buildAttachmentUrl(entry.url, entry.attachmentId, entry.name ?? entry.fileName),
      suggestedLocalFileName: sanitizeFileName(entry.name ?? entry.fileName ?? `${entry.attachmentId}.bin`),
    });
  }

  return {
    attachments,
    recordInlineAttachment,
    recordAttachedFile,
  };
}

function normalizeText(html, collector, source, filePrefix) {
  if (!html) {
    return '';
  }

  const withImageMarkers = html.replace(IMAGE_TAG_PATTERN, (fullMatch, url) => {
    const attachmentId = collector.recordInlineAttachment(url, source, 'inlineImage', filePrefix);
    if (!attachmentId) {
      return ' ';
    }

    return ` [IMGID:${attachmentId}] `;
  });

  return decodeHtml(withImageMarkers)
    .replace(/<\/(div|p|h1|h2|h3|h4|h5|h6|li|ul|ol|tr)>/gi, '\n')
    .replace(/<br\s*\/?>/gi, '\n')
    .replace(/<li[^>]*>/gi, '- ')
    .replace(/<a [^>]*>/gi, '')
    .replace(/<\/a>/gi, '')
    .replace(/<[^>]+>/g, ' ')
    .replace(/\r/g, '')
    .replace(/[ \t]+/g, ' ')
    .replace(/ *\n */g, '\n')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}

function extractLegacyAttachedFiles(workItemSource) {
  return Array.isArray(workItemSource.attachedFiles) ? workItemSource.attachedFiles : [];
}

function extractRelationAttachedFiles(workItemSource) {
  if (!Array.isArray(workItemSource.relations)) {
    return [];
  }

  return workItemSource.relations
    .filter((relation) => relation.rel === 'AttachedFile')
    .map((relation) => ({
      attachmentId: relation.url?.split('/').pop(),
      fileName: relation.attributes?.name,
      url: relation.url,
      source: 'relation:AttachedFile',
    }));
}

function extractWorkItemFields(workItemSource) {
  if (workItemSource.fields) {
    return {
      IterationPath: workItemSource.fields['System.IterationPath'] ?? '',
      State: workItemSource.fields['System.State'] ?? '',
      AssignedTo: readAssignedToValue(workItemSource.fields['System.AssignedTo']),
      Title: workItemSource.fields['System.Title'] ?? '',
      DescriptionHtml: workItemSource.fields['System.Description'] ?? '',
      AcceptanceCriteriaHtml: workItemSource.fields['Microsoft.VSTS.Common.AcceptanceCriteria'] ?? '',
      workItemId: workItemSource.id,
    };
  }

  return {
    IterationPath: workItemSource.IterationPath ?? workItemSource.iterationPath ?? '',
    State: workItemSource.State ?? workItemSource.state ?? '',
    AssignedTo: workItemSource.AssignedTo ?? workItemSource.assignedTo ?? '',
    Title: workItemSource.Title ?? workItemSource.title ?? '',
    DescriptionHtml: workItemSource.descriptionHtml ?? workItemSource.Description ?? '',
    AcceptanceCriteriaHtml: workItemSource.acceptanceCriteriaHtml ?? workItemSource.AcceptanceCriteria ?? '',
    workItemId: workItemSource.id ?? workItemSource.workItemId,
  };
}

function extractComments(commentsSource, workItemSource) {
  if (commentsSource?.comments && Array.isArray(commentsSource.comments)) {
    return commentsSource.comments;
  }

  if (Array.isArray(workItemSource.Comment)) {
    return workItemSource.Comment.map((comment, index) => ({
      id: comment.id ?? index,
      createdDate: comment.CreatedDate,
      createdBy: { displayName: comment.CreatedBy },
      text: comment.Text,
    }));
  }

  return [];
}

async function readJson(filePath) {
  return JSON.parse(await fs.readFile(filePath, 'utf8'));
}

async function readPreviousManifest(rawDir, preserveExistingStatus) {
  if (!preserveExistingStatus) {
    return new Map();
  }

  try {
    const previous = await readJson(path.join(rawDir, 'attachments.json'));
    return new Map((previous.attachments ?? []).map((entry) => [entry.attachmentId, entry]));
  } catch {
    return new Map();
  }
}

async function writeNormalizedFiles(rawDir, normalizedWorkItem, attachmentEntries) {
  await fs.mkdir(rawDir, { recursive: true });
  await fs.rm(path.join(rawDir, 'comments.json'), { force: true });

  const attachmentsManifest = {
    workItemId: normalizedWorkItem.workItemId,
    attachmentCount: attachmentEntries.length,
    attachments: attachmentEntries.map((entry) => ({
      attachmentId: entry.attachmentId,
      'attachment analysis': entry.attachmentAnalysis,
    })),
  };

  const workItemOutput = {
    IterationPath: normalizedWorkItem.IterationPath,
    State: normalizedWorkItem.State,
    AssignedTo: normalizedWorkItem.AssignedTo,
    Title: normalizedWorkItem.Title,
    Description: normalizedWorkItem.Description,
    AcceptanceCriteria: normalizedWorkItem.AcceptanceCriteria,
    Comment: normalizedWorkItem.Comment,
  };

  await fs.writeFile(path.join(rawDir, 'work-item.json'), `${JSON.stringify(workItemOutput, null, 2)}\n`, 'utf8');
  await fs.writeFile(path.join(rawDir, 'attachments.json'), `${JSON.stringify(attachmentsManifest, null, 2)}\n`, 'utf8');
}

async function main() {
  const options = parseArguments(process.argv.slice(2));
  const workItemSource = await readJson(options.workItemFile);
  const commentsSource = options.commentsFile ? await readJson(options.commentsFile) : undefined;
  const previousManifest = await readPreviousManifest(options.rawDir, options.preserveExistingStatus);
  const collector = createAttachmentCollector(previousManifest);
  const workItemFields = extractWorkItemFields(workItemSource);

  for (const entry of extractLegacyAttachedFiles(workItemSource)) {
    collector.recordAttachedFile(entry);
  }

  for (const entry of extractRelationAttachedFiles(workItemSource)) {
    collector.recordAttachedFile(entry);
  }

  const normalizedWorkItem = {
    ...workItemFields,
    Description: normalizeText(workItemFields.DescriptionHtml, collector, 'System.Description', 'description'),
    AcceptanceCriteria: normalizeText(
      workItemFields.AcceptanceCriteriaHtml,
      collector,
      'Microsoft.VSTS.Common.AcceptanceCriteria',
      'acceptance_criteria'
    ),
    Comment: extractComments(commentsSource, workItemSource).map((comment, index) => ({
      CreatedDate: comment.createdDate ?? comment.CreatedDate ?? '',
      CreatedBy: comment.createdBy?.displayName ?? comment.CreatedBy ?? '',
      Text: normalizeText(comment.text ?? comment.Text ?? '', collector, `comment:${comment.id ?? index}`, `comment_${comment.id ?? index}`),
    })),
  };

  await writeNormalizedFiles(options.rawDir, normalizedWorkItem, [...collector.attachments.values()]);
  console.log(`Normalized Azure DevOps story payload into ${options.rawDir}.`);
}

main().catch((error) => {
  console.error(error.message);
  process.exitCode = 1;
});